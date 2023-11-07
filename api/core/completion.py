from __future__ import annotations

import json
import concurrent
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Union, Tuple

from flask import current_app, Flask
from requests.exceptions import ChunkedEncodingError

from core.agent.agent_executor import AgentExecuteResult, PlanningStrategy
from core.callback_handler.main_chain_gather_callback_handler import MainChainGatherCallbackHandler
from core.callback_handler.llm_callback_handler import LLMCallbackHandler
from core.conversation_message_task import ConversationMessageTask, ConversationTaskStoppedException, \
    ConversationTaskInterruptException
from core.external_data_tool.factory import ExternalDataToolFactory
from core.model_providers.error import LLMBadRequestError
from core.memory.read_only_conversation_token_db_buffer_shared_memory import \
    ReadOnlyConversationTokenDBBufferSharedMemory
from core.memory.read_only_conversation_summary_buffer_shared_memory import ReadOnlyConversationSummaryBufferSharedMemory
from core.helper import encrypter
from core.model_providers.model_factory import ModelFactory
from core.model_providers.models.entity.message import PromptMessage
from core.model_providers.models.llm.base import BaseLLM
from core.orchestrator_rule_parser import OrchestratorRuleParser
from core.prompt.prompt_template import PromptTemplateParser
from core.prompt.prompt_transform import PromptTransform
from models.model import App, AppModelConfig, Account, Conversation, EndUser
from core.prompt.prompt_builder import PromptBuilder
# from core.prompt.prompts import MORE_LIKE_THIS_GENERATE_PROMPT
from models.dataset import DocumentSegment, Dataset, Document
from models.model import App, AppModelConfig, Account, Conversation, Message, EndUser
from mylogger import logger
from core.moderation.base import ModerationException, ModerationAction
from core.moderation.factory import ModerationFactory


class Completion:
    @classmethod
    def generate(cls, task_id: str, app: App, app_model_config: AppModelConfig, query: str, inputs: dict,
                 user: Union[Account, EndUser], conversation: Optional[Conversation], streaming: bool,
                 is_override: bool = False, retriever_from: str = 'dev',
                 outer_memory: Optional[list] = None,
                 assistant_name: str = None,
                 user_name: str = None,
                 is_new_message=True):
        """
        errors: ProviderTokenNotInitError
        """
        query = PromptTemplateParser.remove_template_variables(query)

        memory = None
        early_stop = None
        if conversation:
            # get memory of conversation (read-only)
            memory = cls.get_memory_from_conversation(
                tenant_id=app.tenant_id,
                app_model_config=app_model_config,
                conversation=conversation,
                return_messages=False,
                human_prefic=user_name,
                assistant_name=assistant_name if assistant_name else "Assistant"
            )

            inputs = conversation.inputs

        final_model_instance = ModelFactory.get_text_generation_model_from_model_config(
            tenant_id=app.tenant_id,
            model_config=app_model_config.model_dict,
            streaming=streaming
        )

        conversation_message_task = ConversationMessageTask(
            task_id=task_id,
            app=app,
            app_model_config=app_model_config,
            user=user,
            conversation=conversation,
            is_override=is_override,
            inputs=inputs,
            query=query,
            streaming=streaming,
            model_instance=final_model_instance,
            user_name=user_name if user_name else "Human",
            is_new_message=is_new_message
        )

        rest_tokens_for_context_and_memory = cls.get_validate_rest_tokens(
            mode=app.mode,
            model_instance=final_model_instance,
            app_model_config=app_model_config,
            query=query,
            inputs=inputs,
            outer_memory=outer_memory,
            assistant_name=assistant_name,
            user_name=user_name
        )

        # init orchestrator rule parser
        orchestrator_rule_parser = OrchestratorRuleParser(
            tenant_id=app.tenant_id,
            app_model_config=app_model_config
        )

        try:
            chain_callback = MainChainGatherCallbackHandler(conversation_message_task)
            # sensitive_word_avoidance_chain = orchestrator_rule_parser.to_sensitive_word_avoidance_chain(
            #     final_model_instance, [chain_callback])

            # if sensitive_word_avoidance_chain:
            #     try:
            #         query = sensitive_word_avoidance_chain.run(query)
            #     except SensitiveWordAvoidanceError as ex:
            #         cls.run_final_llm(
            #             model_instance=final_model_instance,
            #             mode=app.mode,
            #             app_model_config=app_model_config,
            #             query=query,
            #             inputs=inputs,
            #             agent_execute_result=None,
            #             conversation_message_task=conversation_message_task,
            #             memory=memory,
            #             fake_response=ex.message,
            #             outer_memory=outer_memory,
            #             assistant_name=assistant_name,
            #             user_name=user_name
            #         )
            #         return

            # try:
            #     # process sensitive_word_avoidance
            #     inputs, query = cls.moderation_for_inputs(app.id, app.tenant_id, app_model_config, inputs, query)
            # except ModerationException as e:
            #     cls.run_final_llm(
            #         model_instance=final_model_instance,
            #         mode=app.mode,
            #         app_model_config=app_model_config,
            #         query=query,
            #         inputs=inputs,
            #         agent_execute_result=None,
            #         conversation_message_task=conversation_message_task,
            #         memory=memory,
            #         fake_response=str(e)
            #     )
            #     return

            # fill in variable inputs from external data tools if exists
            # external_data_tools = app_model_config.external_data_tools_list
            # if external_data_tools:
            #     inputs = cls.fill_in_inputs_from_external_data_tools(
            #         tenant_id=app.tenant_id,
            #         app_id=app.id,
            #         external_data_tools=external_data_tools,
            #         inputs=inputs,
            #         query=query
            #     )

            # get agent executor
            agent_executor = orchestrator_rule_parser.to_agent_executor(
                conversation_message_task=conversation_message_task,
                memory=memory,
                rest_tokens=rest_tokens_for_context_and_memory,
                chain_callback=chain_callback,
                retriever_from=retriever_from
            )

            query_for_agent = cls.get_query_for_agent(app, app_model_config, query, inputs)

            # run agent executor
            agent_execute_result = None
            if query_for_agent and agent_executor:
                should_use_agent = agent_executor.should_use_agent(query_for_agent)
                if should_use_agent:
                    agent_execute_result = agent_executor.run(query_for_agent)

            # When no extra pre prompt is specified,
            # the output of the agent can be used directly as the main output content without calling LLM again
            fake_response = None
            if not app_model_config.pre_prompt and agent_execute_result and agent_execute_result.output \
                    and agent_execute_result.strategy not in [PlanningStrategy.ROUTER,
                                                              PlanningStrategy.REACT_ROUTER]:
                fake_response = agent_execute_result.output

            # run the final llm
            cls.run_final_llm(
                model_instance=final_model_instance,
                mode=app.mode,
                app_model_config=app_model_config,
                query=query,
                inputs=inputs,
                agent_execute_result=agent_execute_result,
                conversation_message_task=conversation_message_task,
                memory=memory,
                fake_response=fake_response,
                outer_memory=outer_memory,
                user_name=user_name,
                assistant_name=assistant_name
            )
        except (ConversationTaskInterruptException, ConversationTaskStoppedException):
            return
        except ChunkedEncodingError as e:
            # Interrupt by LLM (like OpenAI), handle it.
            logging.warning(f'ChunkedEncodingError: {e}')
            conversation_message_task.end()
            return

    @classmethod
    def moderation_for_inputs(cls, app_id: str, tenant_id: str, app_model_config: AppModelConfig, inputs: dict, query: str):
        if not app_model_config.sensitive_word_avoidance_dict['enabled']:
            return inputs, query

        type = app_model_config.sensitive_word_avoidance_dict['type']

        moderation = ModerationFactory(type, app_id, tenant_id, app_model_config.sensitive_word_avoidance_dict['config'])
        moderation_result = moderation.moderation_for_inputs(inputs, query)

        if not moderation_result.flagged:
            return inputs, query

        if moderation_result.action == ModerationAction.DIRECT_OUTPUT:
            raise ModerationException(moderation_result.preset_response)
        elif moderation_result.action == ModerationAction.OVERRIDED:
            inputs = moderation_result.inputs
            query = moderation_result.query

        return inputs, query

    @classmethod
    def fill_in_inputs_from_external_data_tools(cls, tenant_id: str, app_id: str, external_data_tools: list[dict],
                                                inputs: dict, query: str) -> dict:
        """
        Fill in variable inputs from external data tools if exists.

        :param tenant_id: workspace id
        :param app_id: app id
        :param external_data_tools: external data tools configs
        :param inputs: the inputs
        :param query: the query
        :return: the filled inputs
        """
        # Group tools by type and config
        grouped_tools = {}
        for tool in external_data_tools:
            if not tool.get("enabled"):
                continue

            tool_key = (tool.get("type"), json.dumps(tool.get("config"), sort_keys=True))
            grouped_tools.setdefault(tool_key, []).append(tool)

        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {}
            for tool in external_data_tools:
                if not tool.get("enabled"):
                    continue

                future = executor.submit(
                    cls.query_external_data_tool, current_app._get_current_object(), tenant_id, app_id, tool,
                    inputs, query
                )

                futures[future] = tool

            for future in concurrent.futures.as_completed(futures):
                tool_variable, result = future.result()
                results[tool_variable] = result

        inputs.update(results)
        return inputs

    @classmethod
    def query_external_data_tool(cls, flask_app: Flask, tenant_id: str, app_id: str, external_data_tool: dict,
                                 inputs: dict, query: str) -> Tuple[Optional[str], Optional[str]]:
        with flask_app.app_context():
            tool_variable = external_data_tool.get("variable")
            tool_type = external_data_tool.get("type")
            tool_config = external_data_tool.get("config")

            external_data_tool_factory = ExternalDataToolFactory(
                name=tool_type,
                tenant_id=tenant_id,
                app_id=app_id,
                variable=tool_variable,
                config=tool_config
            )

            # query external data tool
            result = external_data_tool_factory.query(
                inputs=inputs,
                query=query
            )

            return tool_variable, result

    @classmethod
    def get_query_for_agent(cls, app: App, app_model_config: AppModelConfig, query: str, inputs: dict) -> str:
        if app.mode != 'completion':
            return query

        return inputs.get(app_model_config.dataset_query_variable, "")

    @classmethod
    def run_final_llm(cls, model_instance: BaseLLM, mode: str, app_model_config: AppModelConfig, query: str,
                      inputs: dict,
                      agent_execute_result: Optional[AgentExecuteResult],
                      conversation_message_task: ConversationMessageTask,
                      memory: Optional[ReadOnlyConversationTokenDBBufferSharedMemory],
                      fake_response: Optional[str],
                      outer_memory: Optional[list] = None,
                      assistant_name: str = None,
                      user_name: str = None):
        logger.info(f"memory: {memory}")
        logger.info(f"outer_memory: {outer_memory[:min(len(outer_memory), 2)]}")
        prompt_transform = PromptTransform()

        # get llm prompt
        if app_model_config.prompt_type == 'simple':
            prompt_messages, stop_words = prompt_transform.get_prompt(
                mode=mode,
                pre_prompt=app_model_config.pre_prompt,
                inputs=inputs,
                query=query,
                context=agent_execute_result.output if agent_execute_result else None,
                memory=memory,
                model_instance=model_instance,
                outer_memory=outer_memory,
                assistant_name=assistant_name,
                user_name=user_name
            )
        else:
            prompt_messages = prompt_transform.get_advanced_prompt(
                app_mode=mode,
                app_model_config=app_model_config,
                inputs=inputs,
                query=query,
                context=agent_execute_result.output if agent_execute_result else None,
                memory=memory,
                model_instance=model_instance,
                outer_memory=outer_memory,
                assistant_name=assistant_name,
                user_name=user_name
            )

            model_config = app_model_config.model_dict
            completion_params = model_config.get("completion_params", {})
            stop_words = completion_params.get("stop", [])

        logger.info(f"prompt_messages: {prompt_messages[0].content}")
        logger.info(f"stop_words: {stop_words}")

        cls.recale_llm_max_tokens(
            model_instance=model_instance,
            prompt_messages=prompt_messages,
        )

        response = model_instance.run(
            messages=prompt_messages,
            stop=stop_words if stop_words else None,
            callbacks=[LLMCallbackHandler(model_instance, conversation_message_task)],
            fake_response=fake_response
        )
        logger.info(f"model_instance:{model_instance.name} prompt_tokens: {response.prompt_tokens} completion_tokens: {response.completion_tokens} content: {response.content}")
        return response

    @classmethod
    def get_history_messages_from_memory(cls, memory: ReadOnlyConversationTokenDBBufferSharedMemory,
                                         max_token_limit: int) -> str:
        """Get memory messages."""
        memory.max_token_limit = max_token_limit
        memory_key = memory.memory_variables[0]
        external_context = memory.load_memory_variables({})
        return external_context[memory_key]

    @classmethod
    def get_memory_from_conversation(cls, tenant_id: str, app_model_config: AppModelConfig,
                                     conversation: Conversation,
                                     **kwargs) -> ReadOnlyConversationTokenDBBufferSharedMemory:
        # only for calc token in memory
        memory_model_instance = ModelFactory.get_text_generation_model_from_model_config(
            tenant_id=tenant_id,
            model_config=app_model_config.model_dict
        )
        # try:
        #     from langchain.llms import OpenAI
        #     llm = OpenAI(openai_api_key=memory_model_instance.credentials["openai_api_key"])
        # except:
        #     llm = None
        # if llm:
        #     memory = ReadOnlyConversationSummaryBufferSharedMemory(
        #         llm=llm,
        #         conversation=conversation,
        #         model_instance=memory_model_instance,
        #         max_token_limit=kwargs.get("max_token_limit", 20),
        #         memory_key=kwargs.get("memory_key", "chat_history"),
        #         return_messages=kwargs.get("return_messages", True),
        #         input_key=kwargs.get("input_key", "input"),
        #         output_key=kwargs.get("output_key", "output"),
        #         message_limit=kwargs.get("message_limit", 100),
        #         human_prefix=kwargs.get("human_prefix", "Human"),
        #         ai_prefix=kwargs.get("assistant_name", None),
        #         moving_summary_buffer="",
        #         vebrose=True
        #     )
        # else:
        memory = ReadOnlyConversationTokenDBBufferSharedMemory(
            conversation=conversation,
            model_instance=memory_model_instance,
            max_token_limit=kwargs.get("max_token_limit", 1500),
            memory_key=kwargs.get("memory_key", "chat_history"),
            return_messages=kwargs.get("return_messages", True),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output"),
            message_limit=kwargs.get("message_limit", 50),
            human_prefix=kwargs.get("human_prefix", "Human"),
            ai_prefix=kwargs.get("assistant_name", None),
            moving_summary_buffer="",
            # vebrose=True
        )

        return memory

    @classmethod
    def get_validate_rest_tokens(cls, mode: str, model_instance: BaseLLM, app_model_config: AppModelConfig,
                                 query: str, inputs: dict,
                                 outer_memory: Optional[list] = None,
                                 assistant_name: str = None,
                                 user_name: str = None) -> int:
        model_limited_tokens = model_instance.model_rules.max_tokens.max
        max_tokens = model_instance.get_model_kwargs().max_tokens

        if model_limited_tokens is None:
            return -1

        if max_tokens is None:
            max_tokens = 0

        prompt_transform = PromptTransform()
        prompt_messages = []

        # get prompt without memory and context
        if app_model_config.prompt_type == 'simple':
            prompt_messages, _ = prompt_transform.get_prompt(
                mode=mode,
                pre_prompt=app_model_config.pre_prompt,
                inputs=inputs,
                query=query,
                context=None,
                memory=None,
                model_instance=model_instance,
                outer_memory=outer_memory,
                assistant_name=assistant_name,
                user_name=user_name
            )
        else:
            prompt_messages = prompt_transform.get_advanced_prompt(
                app_mode=mode,
                app_model_config=app_model_config,
                inputs=inputs,
                query=query,
                context=None,
                memory=None,
                model_instance=model_instance,
                outer_memory=outer_memory,
                assistant_name=assistant_name,
                user_name=user_name
            )

        prompt_tokens = model_instance.get_num_tokens(prompt_messages)
        rest_tokens = model_limited_tokens - max_tokens - prompt_tokens
        if rest_tokens < 0:
            raise LLMBadRequestError("Query or prefix prompt is too long, you can reduce the prefix prompt, "
                                     "or shrink the max token, or switch to a llm with a larger token limit size.")

        return rest_tokens

    @classmethod
    def recale_llm_max_tokens(cls, model_instance: BaseLLM, prompt_messages: List[PromptMessage]):
        # recalc max_tokens if sum(prompt_token +  max_tokens) over model token limit
        model_limited_tokens = model_instance.model_rules.max_tokens.max
        max_tokens = model_instance.get_model_kwargs().max_tokens

        if model_limited_tokens is None:
            return

        if max_tokens is None:
            max_tokens = 0

        prompt_tokens = model_instance.get_num_tokens(prompt_messages)

        if prompt_tokens + max_tokens > model_limited_tokens:
            max_tokens = max(model_limited_tokens - prompt_tokens, 16)

            # update model instance max tokens
            model_kwargs = model_instance.get_model_kwargs()
            model_kwargs.max_tokens = max_tokens
            model_instance.set_model_kwargs(model_kwargs)

    # @classmethod
    # def generate_more_like_this(cls, task_id: str, app: App, message: Message, pre_prompt: str,
    #                             app_model_config: AppModelConfig, user: Account, streaming: bool):
    #
    #     final_model_instance = ModelFactory.get_text_generation_model_from_model_config(
    #         tenant_id=app.tenant_id,
    #         model_config=app_model_config.model_dict,
    #         streaming=streaming
    #     )
    #
    #     # get llm prompt
    #     old_prompt_messages, _ = final_model_instance.get_prompt(
    #         mode='completion',
    #         pre_prompt=pre_prompt,
    #         inputs=message.inputs,
    #         query=message.query,
    #         context=None,
    #         memory=None
    #     )
    #
    #     original_completion = message.answer.strip()
    #
    #     prompt = MORE_LIKE_THIS_GENERATE_PROMPT
    #     prompt = prompt.format(prompt=old_prompt_messages[0].content, original_completion=original_completion)
    #
    #     prompt_messages = [PromptMessage(content=prompt)]
    #
    #     conversation_message_task = ConversationMessageTask(
    #         task_id=task_id,
    #         app=app,
    #         app_model_config=app_model_config,
    #         user=user,
    #         inputs=message.inputs,
    #         query=message.query,
    #         is_override=True if message.override_model_configs else False,
    #         streaming=streaming,
    #         model_instance=final_model_instance
    #     )
    #
    #     cls.recale_llm_max_tokens(
    #         model_instance=final_model_instance,
    #         prompt_messages=prompt_messages
    #     )
    #
    #     final_model_instance.run(
    #         messages=prompt_messages,
    #         callbacks=[LLMCallbackHandler(final_model_instance, conversation_message_task)]
    #     )
