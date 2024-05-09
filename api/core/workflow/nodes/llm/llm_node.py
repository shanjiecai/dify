import threading
import time
from collections.abc import Generator
from typing import Optional, cast

from flask.ctx import AppContext

from controllers.app_api.img.utils import generate_plan_img_pipeline
from core.app.entities.app_invoke_entities import ModelConfigWithCredentialsEntity
from core.app.entities.queue_entities import QueueRetrieverResourcesEvent
from core.entities.model_entities import ModelStatus
from core.entities.provider_entities import QuotaUnit
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.file.file_obj import FileVar
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_manager import ModelInstance, ModelManager
from core.model_runtime.entities.llm_entities import LLMUsage
from core.model_runtime.entities.message_entities import PromptMessage, PromptMessageContentType
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.model_providers.__base.large_language_model import LargeLanguageModel
from core.model_runtime.utils.encoders import jsonable_encoder
from core.prompt.advanced_prompt_transform import AdvancedPromptTransform
from core.prompt.entities.advanced_prompt_entities import CompletionModelPromptTemplate, MemoryConfig
from core.prompt.utils.prompt_message_util import PromptMessageUtil
from core.workflow.entities.base_node_data_entities import BaseNodeData
from core.workflow.entities.node_entities import NodeRunMetadataKey, NodeRunResult, NodeType, SystemVariable
from core.workflow.entities.variable_pool import VariablePool
from core.workflow.nodes.base_node import BaseNode
from core.workflow.nodes.llm.entities import LLMNodeData, ModelConfig
from core.workflow.utils.variable_template_parser import VariableTemplateParser
from extensions.ext_database import db
from models.model import Conversation, ConversationPlanDetail
from models.provider import Provider, ProviderType
from models.workflow import WorkflowNodeExecutionStatus
from mylogger import logger
from services.conversation_service import ConversationService


def _plan_finish_question(conversation: Conversation, main_context: AppContext):
    """
    Plan finish question
    :param conversation: conversation
    :return:
    """
    with main_context:
        plan_detail_list = []
        plan_detail, plan, history_str = ConversationService.generate_plan(conversation.id,
                                                                          plan=conversation.plan_question_invoke_plan)
        plan_detail_list.append(plan_detail)
        logger.info(f"generate_plan_from_conversation response: {plan_detail_list}")
        image_list, img_perfect_prompt_list = generate_plan_img_pipeline(
            conversation.plan_question_invoke_plan, model="search_engine")
        # 暂时不去掉plan_question_invoke_plan
        # conversation.plan_question_invoke_plan = None
        conversation.plan_question_invoke_user = None
        conversation.plan_question_invoke_user_id = None
        conversation.plan_question_invoke_time = None
        conversation_plan_detail = ConversationPlanDetail(
            conversation_id=conversation.id,
            plan=plan,
            plan_detail_list=plan_detail_list,
            plan_conversation_history=history_str,
            image_list=image_list,
            img_perfect_prompt_list=img_perfect_prompt_list
        )
        time.sleep(1)
        db.session.add(conversation_plan_detail)
        db.session.add(conversation)
        db.session.commit()


class LLMNode(BaseNode):
    _node_data_cls = LLMNodeData
    node_type = NodeType.LLM
    _conversation: Conversation = None

    def _run(self, variable_pool: VariablePool, **kwargs) -> NodeRunResult:
        """
        Run node
        :param variable_pool: variable pool
        :return:
        """
        if kwargs.get("conversation"):
            self._conversation = kwargs.get("conversation")
        node_data = self.node_data
        node_data = cast(self._node_data_cls, node_data)

        node_inputs = None
        process_data = None

        try:
            # fetch variables and fetch values from variable pool
            inputs = self._fetch_inputs(node_data, variable_pool)

            node_inputs = {}

            # fetch files
            files: list[FileVar] = self._fetch_files(node_data, variable_pool)

            if files:
                node_inputs['#files#'] = [file.to_dict() for file in files]

            # fetch context value
            context = self._fetch_context(node_data, variable_pool)

            if context:
                node_inputs['#context#'] = context

            # fetch model config
            model_instance, model_config = self._fetch_model_config(node_data.model)

            # fetch memory
            memory = self._fetch_memory(node_data.memory, variable_pool, model_instance)

            # fetch prompt messages
            prompt_messages, stop = self._fetch_prompt_messages(
                node_data=node_data,
                query=variable_pool.get_variable_value(['sys', SystemVariable.QUERY.value])
                if node_data.memory else None,
                query_prompt_template=node_data.memory.query_prompt_template if node_data.memory else None,
                inputs=inputs,
                files=files,
                context=context,
                memory=memory,
                model_config=model_config,
                user_name=kwargs.get("user_name", None),
                assistant_name=kwargs.get("assistant_name"),
                conversation=kwargs.get("conversation"),
            )

            process_data = {
                'model_mode': model_config.mode,
                'prompts': PromptMessageUtil.prompt_messages_to_prompt_for_saving(
                    model_mode=model_config.mode,
                    prompt_messages=prompt_messages
                )
            }

            # handle invoke result
            result_text, usage = self._invoke_llm(
                node_data_model=node_data.model,
                model_instance=model_instance,
                prompt_messages=prompt_messages,
                stop=stop
            )
        except Exception as e:
            return NodeRunResult(
                status=WorkflowNodeExecutionStatus.FAILED,
                error=str(e),
                inputs=node_inputs,
                process_data=process_data
            )

        outputs = {
            'text': result_text,
            'usage': jsonable_encoder(usage)
        }

        return NodeRunResult(
            status=WorkflowNodeExecutionStatus.SUCCEEDED,
            inputs=node_inputs,
            process_data=process_data,
            outputs=outputs,
            metadata={
                NodeRunMetadataKey.TOTAL_TOKENS: usage.total_tokens,
                NodeRunMetadataKey.TOTAL_PRICE: usage.total_price,
                NodeRunMetadataKey.CURRENCY: usage.currency
            }
        )

    def _invoke_llm(self, node_data_model: ModelConfig,
                    model_instance: ModelInstance,
                    prompt_messages: list[PromptMessage],
                    stop: list[str]) -> tuple[str, LLMUsage]:
        """
        Invoke large language model
        :param node_data_model: node data model
        :param model_instance: model instance
        :param prompt_messages: prompt messages
        :param stop: stop
        :return:
        """
        db.session.close()

        logger.info(f"[workflow_invoke_llm_prompt]: {prompt_messages}")

        invoke_result = model_instance.invoke_llm(
            prompt_messages=prompt_messages,
            model_parameters=node_data_model.completion_params,
            stop=stop,
            stream=True,
            user=self.user_id,
        )

        # handle invoke result
        text, usage = self._handle_invoke_result(
            invoke_result=invoke_result
        )
        logger.info(f"[workflow_invoke_llm_result]: {text}")
        # 识别末尾的<finish_question>
        if text.__contains__('<finish_question>'):
            logger.info(
                f"remove conversation {self._conversation.id} <finish_question> from {text}")

            # 问题提问结束，删除conversation plan_question
            conversation: Conversation = db.session.query(Conversation).filter(
                Conversation.id == self._conversation.id).first()
            if conversation:
                # threading后台运行
                from flask import current_app
                threading.Thread(target=_plan_finish_question, args=(conversation, current_app._get_current_object().app_context())).start()

        # deduct quota
        self.deduct_llm_quota(tenant_id=self.tenant_id, model_instance=model_instance, usage=usage)

        return text, usage

    def _handle_invoke_result(self, invoke_result: Generator) -> tuple[str, LLMUsage]:
        """
        Handle invoke result
        :param invoke_result: invoke result
        :return:
        """
        model = None
        prompt_messages = []
        full_text = ''
        usage = None
        for result in invoke_result:
            text = result.delta.message.content
            full_text += text

            self.publish_text_chunk(text=text, value_selector=[self.node_id, 'text'])

            if not model:
                model = result.model

            if not prompt_messages:
                prompt_messages = result.prompt_messages

            if not usage and result.delta.usage:
                usage = result.delta.usage

        if not usage:
            usage = LLMUsage.empty_usage()

        return full_text, usage

    def _fetch_inputs(self, node_data: LLMNodeData, variable_pool: VariablePool) -> dict[str, str]:
        """
        Fetch inputs
        :param node_data: node data
        :param variable_pool: variable pool
        :return:
        """
        inputs = {}
        prompt_template = node_data.prompt_template

        variable_selectors = []
        if isinstance(prompt_template, list):
            for prompt in prompt_template:
                variable_template_parser = VariableTemplateParser(template=prompt.text)
                variable_selectors.extend(variable_template_parser.extract_variable_selectors())
        elif isinstance(prompt_template, CompletionModelPromptTemplate):
            variable_template_parser = VariableTemplateParser(template=prompt_template.text)
            variable_selectors = variable_template_parser.extract_variable_selectors()

        for variable_selector in variable_selectors:
            variable_value = variable_pool.get_variable_value(variable_selector.value_selector)
            if variable_value is None:
                raise ValueError(f'Variable {variable_selector.variable} not found')

            inputs[variable_selector.variable] = variable_value

        memory = node_data.memory
        if memory and memory.query_prompt_template:
            query_variable_selectors = (VariableTemplateParser(template=memory.query_prompt_template)
                                        .extract_variable_selectors())
            for variable_selector in query_variable_selectors:
                variable_value = variable_pool.get_variable_value(variable_selector.value_selector)
                if variable_value is None:
                    raise ValueError(f'Variable {variable_selector.variable} not found')

                inputs[variable_selector.variable] = variable_value

        return inputs

    def _fetch_files(self, node_data: LLMNodeData, variable_pool: VariablePool) -> list[FileVar]:
        """
        Fetch files
        :param node_data: node data
        :param variable_pool: variable pool
        :return:
        """
        if not node_data.vision.enabled:
            return []

        files = variable_pool.get_variable_value(['sys', SystemVariable.FILES.value])
        if not files:
            return []

        return files

    def _fetch_context(self, node_data: LLMNodeData, variable_pool: VariablePool) -> Optional[str]:
        """
        Fetch context
        :param node_data: node data
        :param variable_pool: variable pool
        :return:
        """
        if not node_data.context.enabled:
            return None

        if not node_data.context.variable_selector:
            return None

        context_value = variable_pool.get_variable_value(node_data.context.variable_selector)
        if context_value:
            if isinstance(context_value, str):
                return context_value
            elif isinstance(context_value, list):
                context_str = ''
                original_retriever_resource = []
                for item in context_value:
                    if isinstance(item, str):
                        context_str += item + '\n'
                    else:
                        if 'content' not in item:
                            raise ValueError(f'Invalid context structure: {item}')

                        context_str += item['content'] + '\n'

                        retriever_resource = self._convert_to_original_retriever_resource(item)
                        if retriever_resource:
                            original_retriever_resource.append(retriever_resource)

                if self.callbacks and original_retriever_resource:
                    for callback in self.callbacks:
                        callback.on_event(
                            event=QueueRetrieverResourcesEvent(
                                retriever_resources=original_retriever_resource
                            )
                        )

                return context_str.strip()

        return None

    def _convert_to_original_retriever_resource(self, context_dict: dict) -> Optional[dict]:
        """
        Convert to original retriever resource, temp.
        :param context_dict: context dict
        :return:
        """
        if ('metadata' in context_dict and '_source' in context_dict['metadata']
                and context_dict['metadata']['_source'] == 'knowledge'):
            metadata = context_dict.get('metadata', {})
            source = {
                'position': metadata.get('position'),
                'dataset_id': metadata.get('dataset_id'),
                'dataset_name': metadata.get('dataset_name'),
                'document_id': metadata.get('document_id'),
                'document_name': metadata.get('document_name'),
                'data_source_type': metadata.get('document_data_source_type'),
                'segment_id': metadata.get('segment_id'),
                'retriever_from': metadata.get('retriever_from'),
                'score': metadata.get('score'),
                'hit_count': metadata.get('segment_hit_count'),
                'word_count': metadata.get('segment_word_count'),
                'segment_position': metadata.get('segment_position'),
                'index_node_hash': metadata.get('segment_index_node_hash'),
                'content': context_dict.get('content'),
            }

            return source

        return None

    def _fetch_model_config(self, node_data_model: ModelConfig) -> tuple[
        ModelInstance, ModelConfigWithCredentialsEntity]:
        """
        Fetch model config
        :param node_data_model: node data model
        :return:
        """
        model_name = node_data_model.name
        provider_name = node_data_model.provider

        model_manager = ModelManager()
        model_instance = model_manager.get_model_instance(
            tenant_id=self.tenant_id,
            model_type=ModelType.LLM,
            provider=provider_name,
            model=model_name
        )

        provider_model_bundle = model_instance.provider_model_bundle
        model_type_instance = model_instance.model_type_instance
        model_type_instance = cast(LargeLanguageModel, model_type_instance)

        model_credentials = model_instance.credentials

        # check model
        provider_model = provider_model_bundle.configuration.get_provider_model(
            model=model_name,
            model_type=ModelType.LLM
        )

        if provider_model is None:
            raise ValueError(f"Model {model_name} not exist.")

        if provider_model.status == ModelStatus.NO_CONFIGURE:
            raise ProviderTokenNotInitError(f"Model {model_name} credentials is not initialized.")
        elif provider_model.status == ModelStatus.NO_PERMISSION:
            raise ModelCurrentlyNotSupportError(f"Dify Hosted OpenAI {model_name} currently not support.")
        elif provider_model.status == ModelStatus.QUOTA_EXCEEDED:
            raise QuotaExceededError(f"Model provider {provider_name} quota exceeded.")

        # model config
        completion_params = node_data_model.completion_params
        stop = []
        if 'stop' in completion_params:
            stop = completion_params['stop']
            del completion_params['stop']

        # get model mode
        model_mode = node_data_model.mode
        if not model_mode:
            raise ValueError("LLM mode is required.")

        model_schema = model_type_instance.get_model_schema(
            model_name,
            model_credentials
        )

        if not model_schema:
            raise ValueError(f"Model {model_name} not exist.")

        return model_instance, ModelConfigWithCredentialsEntity(
            provider=provider_name,
            model=model_name,
            model_schema=model_schema,
            mode=model_mode,
            provider_model_bundle=provider_model_bundle,
            credentials=model_credentials,
            parameters=completion_params,
            stop=stop,
        )

    def _fetch_memory(self, node_data_memory: Optional[MemoryConfig],
                      variable_pool: VariablePool,
                      model_instance: ModelInstance) -> Optional[TokenBufferMemory]:
        """
        Fetch memory
        :param node_data_memory: node data memory
        :param variable_pool: variable pool
        :return:
        """
        if not node_data_memory:
            return None

        # get conversation id
        conversation_id = variable_pool.get_variable_value(['sys', SystemVariable.CONVERSATION_ID.value])
        if conversation_id is None:
            return None

        # get conversation
        conversation = db.session.query(Conversation).filter(
            # Conversation.app_id == self.app_id,
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return None

        memory = TokenBufferMemory(
            conversation=conversation,
            model_instance=model_instance
        )

        return memory

    def _fetch_prompt_messages(self, node_data: LLMNodeData,
                               query: Optional[str],
                               query_prompt_template: Optional[str],
                               inputs: dict[str, str],
                               files: list[FileVar],
                               context: Optional[str],
                               memory: Optional[TokenBufferMemory],
                               model_config: ModelConfigWithCredentialsEntity,
                               assistant_name: Optional[str] = None,
                               user_name: Optional[str] = None,
                               conversation: Conversation = None,
                               )\
            -> tuple[list[PromptMessage], Optional[list[str]]]:
        """
        Fetch prompt messages
        :param node_data: node data
        :param query: query
        :param query_prompt_template: query prompt template
        :param inputs: inputs
        :param files: files
        :param context: context
        :param memory: memory
        :param model_config: model config
        :param assistant_name: assistant name
        :param user_name: user name
        :param conversation: conversation
        :return:
        """
        prompt_transform = AdvancedPromptTransform(with_variable_tmpl=True)
        prompt_messages = prompt_transform.get_prompt(
            prompt_template=node_data.prompt_template,
            inputs=inputs,
            query=query if query else '',
            files=files,
            context=context,
            memory_config=node_data.memory,
            memory=memory,
            model_config=model_config,
            query_prompt_template=query_prompt_template,
            conversation=conversation,
            assistant_name=assistant_name,
            user_name=user_name,
        )
        stop = model_config.stop

        vision_enabled = node_data.vision.enabled
        filtered_prompt_messages = []
        for prompt_message in prompt_messages:
            if prompt_message.is_empty():
                continue

            if not isinstance(prompt_message.content, str):
                prompt_message_content = []
                for content_item in prompt_message.content:
                    if vision_enabled and content_item.type == PromptMessageContentType.IMAGE:
                        prompt_message_content.append(content_item)
                    elif content_item.type == PromptMessageContentType.TEXT:
                        prompt_message_content.append(content_item)

                if len(prompt_message_content) > 1:
                    prompt_message.content = prompt_message_content
                elif (len(prompt_message_content) == 1
                      and prompt_message_content[0].type == PromptMessageContentType.TEXT):
                    prompt_message.content = prompt_message_content[0].data

            filtered_prompt_messages.append(prompt_message)

        if not filtered_prompt_messages:
            raise ValueError("No prompt found in the LLM configuration. "
                             "Please ensure a prompt is properly configured before proceeding.")

        return filtered_prompt_messages, stop

    @classmethod
    def deduct_llm_quota(cls, tenant_id: str, model_instance: ModelInstance, usage: LLMUsage) -> None:
        """
        Deduct LLM quota
        :param tenant_id: tenant id
        :param model_instance: model instance
        :param usage: usage
        :return:
        """
        provider_model_bundle = model_instance.provider_model_bundle
        provider_configuration = provider_model_bundle.configuration

        if provider_configuration.using_provider_type != ProviderType.SYSTEM:
            return

        system_configuration = provider_configuration.system_configuration

        quota_unit = None
        for quota_configuration in system_configuration.quota_configurations:
            if quota_configuration.quota_type == system_configuration.current_quota_type:
                quota_unit = quota_configuration.quota_unit

                if quota_configuration.quota_limit == -1:
                    return

                break

        used_quota = None
        if quota_unit:
            if quota_unit == QuotaUnit.TOKENS:
                used_quota = usage.total_tokens
            elif quota_unit == QuotaUnit.CREDITS:
                used_quota = 1

                if 'gpt-4' in model_instance.model:
                    used_quota = 20
            else:
                used_quota = 1

        if used_quota is not None:
            db.session.query(Provider).filter(
                Provider.tenant_id == tenant_id,
                Provider.provider_name == model_instance.provider,
                Provider.provider_type == ProviderType.SYSTEM.value,
                Provider.quota_type == system_configuration.current_quota_type.value,
                Provider.quota_limit > Provider.quota_used
            ).update({'quota_used': Provider.quota_used + used_quota})
            db.session.commit()

    @classmethod
    def _extract_variable_selector_to_variable_mapping(cls, node_data: BaseNodeData) -> dict[str, list[str]]:
        """
        Extract variable selector to variable mapping
        :param node_data: node data
        :return:
        """
        node_data = node_data
        node_data = cast(cls._node_data_cls, node_data)

        prompt_template = node_data.prompt_template

        variable_selectors = []
        if isinstance(prompt_template, list):
            for prompt in prompt_template:
                variable_template_parser = VariableTemplateParser(template=prompt.text)
                variable_selectors.extend(variable_template_parser.extract_variable_selectors())
        else:
            variable_template_parser = VariableTemplateParser(template=prompt_template.text)
            variable_selectors = variable_template_parser.extract_variable_selectors()

        variable_mapping = {}
        for variable_selector in variable_selectors:
            variable_mapping[variable_selector.variable] = variable_selector.value_selector

        memory = node_data.memory
        if memory and memory.query_prompt_template:
            query_variable_selectors = (VariableTemplateParser(template=memory.query_prompt_template)
                                        .extract_variable_selectors())
            for variable_selector in query_variable_selectors:
                variable_mapping[variable_selector.variable] = variable_selector.value_selector

        if node_data.context.enabled:
            variable_mapping['#context#'] = node_data.context.variable_selector

        if node_data.vision.enabled:
            variable_mapping['#files#'] = ['sys', SystemVariable.FILES.value]

        if node_data.memory:
            variable_mapping['#sys.query#'] = ['sys', SystemVariable.QUERY.value]

        return variable_mapping

    @classmethod
    def get_default_config(cls, filters: Optional[dict] = None) -> dict:
        """
        Get default config of node.
        :param filters: filter by node config parameters.
        :return:
        """
        return {
            "type": "llm",
            "config": {
                "prompt_templates": {
                    "chat_model": {
                        "prompts": [
                            {
                                "role": "system",
                                "text": "You are a helpful AI assistant."
                            }
                        ]
                    },
                    "completion_model": {
                        "conversation_histories_role": {
                            "user_prefix": "Human",
                            "assistant_prefix": "Assistant"
                        },
                        "prompt": {
                            "text": "Here is the chat histories between human and assistant, inside "
                                    "<histories></histories> XML tags.\n\n<histories>\n{{"
                                    "#histories#}}\n</histories>\n\n\nHuman: {{#sys.query#}}\n\nAssistant:"
                        },
                        "stop": ["Human:"]
                    }
                }
            }
        }
