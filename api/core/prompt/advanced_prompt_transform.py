import datetime
from typing import Optional, Union

from core.app.entities.app_invoke_entities import ModelConfigWithCredentialsEntity
from core.file.file_obj import FileVar
from core.helper.code_executor.jinja2.jinja2_formatter import Jinja2Formatter
from core.helper.openai_name_convert import correct_name_field
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_runtime.entities.message_entities import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    SystemPromptMessage,
    TextPromptMessageContent,
    UserPromptMessage,
)
from core.prompt.entities.advanced_prompt_entities import (
    ChatModelMessage,
    CompletionModelPromptTemplate,
    MemoryConfig,
)
from core.prompt.prompt_transform import PromptTransform
from core.prompt.simple_prompt_transform import ModelMode
from core.prompt.utils.prompt_template_parser import PromptTemplateParser
from core.prompt_const import plan_question_template
from models.model import Conversation
from mylogger import logger


class AdvancedPromptTransform(PromptTransform):
    """
    Advanced Prompt Transform for Workflow LLM Node.
    """

    def __init__(self, with_variable_tmpl: bool = False) -> None:
        self.with_variable_tmpl = with_variable_tmpl

    def get_prompt(
        self,
        prompt_template: Union[list[ChatModelMessage], CompletionModelPromptTemplate],
        inputs: dict,
        query: str,
        files: list[FileVar],
        context: Optional[str],
        memory_config: Optional[MemoryConfig],
        memory: Optional[TokenBufferMemory],
        model_config: ModelConfigWithCredentialsEntity,
        assistant_name: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation: Conversation = None,
        query_prompt_template: Optional[str] = None,
    ) -> list[PromptMessage]:
        inputs = {key: str(value) for key, value in inputs.items()}

        prompt_messages = []

        model_mode = ModelMode.value_of(model_config.mode)
        if model_mode == ModelMode.COMPLETION:
            prompt_messages = self._get_completion_model_prompt_messages(
                prompt_template=prompt_template,
                inputs=inputs,
                query=query,
                files=files,
                context=context,
                memory_config=memory_config,
                memory=memory,
                model_config=model_config,
            )
        elif model_mode == ModelMode.CHAT:
            prompt_messages = self._get_chat_model_prompt_messages(
                prompt_template=prompt_template,
                inputs=inputs,
                query=query,
                query_prompt_template=query_prompt_template,
                files=files,
                context=context,
                memory_config=memory_config,
                memory=memory,
                model_config=model_config,
                user_name=user_name,
                assistant_name=assistant_name,
                conversation=conversation,
            )

        return prompt_messages

    def _get_completion_model_prompt_messages(
        self,
        prompt_template: CompletionModelPromptTemplate,
        inputs: dict,
        query: Optional[str],
        files: list[FileVar],
        context: Optional[str],
        memory_config: Optional[MemoryConfig],
        memory: Optional[TokenBufferMemory],
        model_config: ModelConfigWithCredentialsEntity,
    ) -> list[PromptMessage]:
        """
        Get completion model prompt messages.
        """
        raw_prompt = prompt_template.text

        prompt_messages = []

        if prompt_template.edition_type == "basic" or not prompt_template.edition_type:
            prompt_template = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
            prompt_inputs = {k: inputs[k] for k in prompt_template.variable_keys if k in inputs}

            prompt_inputs = self._set_context_variable(context, prompt_template, prompt_inputs)

            if memory and memory_config:
                role_prefix = memory_config.role_prefix
                prompt_inputs = self._set_histories_variable(
                    memory=memory,
                    memory_config=memory_config,
                    raw_prompt=raw_prompt,
                    role_prefix=role_prefix,
                    prompt_template=prompt_template,
                    prompt_inputs=prompt_inputs,
                    model_config=model_config,
                )

            if query:
                prompt_inputs = self._set_query_variable(query, prompt_template, prompt_inputs)

            prompt = prompt_template.format(prompt_inputs)
        else:
            prompt = raw_prompt
            prompt_inputs = inputs

            prompt = Jinja2Formatter.format(prompt, prompt_inputs)

        if files:
            prompt_message_contents = [TextPromptMessageContent(data=prompt)]
            for file in files:
                prompt_message_contents.append(file.prompt_message_content)

            prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
        else:
            prompt_messages.append(UserPromptMessage(content=prompt))

        return prompt_messages

    def _get_chat_model_prompt_messages(
        self,
        prompt_template: list[ChatModelMessage],
        inputs: dict,
        query: Optional[str],
        files: list[FileVar],
        context: Optional[str],
        memory_config: Optional[MemoryConfig],
        memory: Optional[TokenBufferMemory],
        model_config: ModelConfigWithCredentialsEntity,
        query_prompt_template: Optional[str] = None,
        assistant_name: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation: Conversation = None,
    ) -> list[PromptMessage]:
        """
        Get chat model prompt messages.
        """
        raw_prompt_list = prompt_template

        prompt_messages = []

        for prompt_item in raw_prompt_list:
            raw_prompt = prompt_item.text

            if prompt_item.edition_type == "basic" or not prompt_item.edition_type:
                prompt_template = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
                prompt_inputs = {k: inputs[k] for k in prompt_template.variable_keys if k in inputs}

                prompt_inputs = self._set_context_variable(context, prompt_template, prompt_inputs)

                prompt = prompt_template.format(prompt_inputs)
            elif prompt_item.edition_type == "jinja2":
                prompt = raw_prompt
                prompt_inputs = inputs

                prompt = Jinja2Formatter.format(prompt, prompt_inputs)
            else:
                raise ValueError(f"Invalid edition type: {prompt_item.edition_type}")

            if prompt_item.role == PromptMessageRole.USER:
                if user_name:
                    prompt_messages.append(UserPromptMessage(content=prompt, name=correct_name_field(user_name)))
                else:
                    prompt_messages.append(UserPromptMessage(content=prompt))
            elif prompt_item.role == PromptMessageRole.SYSTEM and prompt:
                if (
                    conversation
                    and conversation.plan_question
                    and conversation.plan_question_invoke_user
                    and conversation.plan_question_invoke_time
                    > datetime.datetime.utcnow() - datetime.timedelta(hours=16)
                ) and conversation.app_id not in [
                    "a756e5d2-c735-4f68-8db0-1de49333501c",
                    "19d2fd0b-6e1c-47f9-87ab-cc039b6d3881",
                    "4cb1eee5-72d9-4cd6-befc-e4e0d4fb6333",
                    "cee86a23-56ab-4b3d-a548-ca34191b23a1",
                ]:

                    def remove_character_info(text):
                        start_phrase = "character information"
                        end_phrase = "Don’t be verbose or too formal or polite when speaking."
                        start_index = text.find(start_phrase)
                        end_index = text.find(end_phrase)
                        if start_index == -1 or end_index == -1:
                            return text  # 如果没找到起始或结束短语，返回原文本
                        # 删除指定部分
                        return text[:start_index] + text[end_index + len(end_phrase) :]

                    # 去掉人设信息，prompt中 character information:和Don’t be verbose or too formal or polite when speaking之间的内容
                    prompt = remove_character_info(prompt)
                    questions = "\n".join(conversation.plan_question)
                    plan_question_prompt = plan_question_template.format(questions=questions)
                    logger.debug(f"plan_question_prompt: {plan_question_prompt}")
                    prompt += plan_question_prompt
                prompt_messages.append(SystemPromptMessage(content=prompt))
            elif prompt_item.role == PromptMessageRole.ASSISTANT:
                if assistant_name:
                    prompt_messages.append(
                        AssistantPromptMessage(content=prompt, name=correct_name_field(assistant_name))
                    )
                else:
                    prompt_messages.append(AssistantPromptMessage(content=prompt))

        if query and query_prompt_template:
            prompt_template = PromptTemplateParser(
                template=query_prompt_template, with_variable_tmpl=self.with_variable_tmpl
            )
            prompt_inputs = {k: inputs[k] for k in prompt_template.variable_keys if k in inputs}
            prompt_inputs["#sys.query#"] = query

            prompt_inputs = self._set_context_variable(context, prompt_template, prompt_inputs)

            query = prompt_template.format(prompt_inputs)

        if memory and memory_config:
            if conversation and conversation.plan_question:
                # 历史只取十轮
                prompt_messages = self._append_chat_histories(
                    memory, memory_config, prompt_messages, model_config, message_limit=10
                )
            else:
                prompt_messages = self._append_chat_histories(memory, memory_config, prompt_messages, model_config)

            if files:
                prompt_message_contents = [TextPromptMessageContent(data=query)]
                for file in files:
                    prompt_message_contents.append(file.prompt_message_content)

                prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
            else:
                if user_name:
                    prompt_messages.append(UserPromptMessage(content=query, name=correct_name_field(user_name)))
                else:
                    prompt_messages.append(UserPromptMessage(content=query))
        elif files:
            if not query:
                # get last message
                last_message = prompt_messages[-1] if prompt_messages else None
                if last_message and last_message.role == PromptMessageRole.USER:
                    # get last user message content and add files
                    prompt_message_contents = [TextPromptMessageContent(data=last_message.content)]
                    for file in files:
                        prompt_message_contents.append(file.prompt_message_content)

                    last_message.content = prompt_message_contents
                else:
                    prompt_message_contents = [TextPromptMessageContent(data="")]  # not for query
                    for file in files:
                        prompt_message_contents.append(file.prompt_message_content)

                    prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
            else:
                prompt_message_contents = [TextPromptMessageContent(data=query)]
                for file in files:
                    prompt_message_contents.append(file.prompt_message_content)

                prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
        elif query:
            if user_name:
                prompt_messages.append(UserPromptMessage(content=query, name=correct_name_field(user_name)))
            else:
                prompt_messages.append(UserPromptMessage(content=query))

        return prompt_messages

    def _set_context_variable(self, context: str, prompt_template: PromptTemplateParser, prompt_inputs: dict) -> dict:
        if "#context#" in prompt_template.variable_keys:
            if context:
                prompt_inputs["#context#"] = context
            else:
                prompt_inputs["#context#"] = ""

        return prompt_inputs

    def _set_query_variable(self, query: str, prompt_template: PromptTemplateParser, prompt_inputs: dict) -> dict:
        if "#query#" in prompt_template.variable_keys:
            if query:
                prompt_inputs["#query#"] = query
            else:
                prompt_inputs["#query#"] = ""

        return prompt_inputs

    def _set_histories_variable(
        self,
        memory: TokenBufferMemory,
        memory_config: MemoryConfig,
        raw_prompt: str,
        role_prefix: MemoryConfig.RolePrefix,
        prompt_template: PromptTemplateParser,
        prompt_inputs: dict,
        model_config: ModelConfigWithCredentialsEntity,
    ) -> dict:
        if "#histories#" in prompt_template.variable_keys:
            if memory:
                inputs = {"#histories#": "", **prompt_inputs}
                prompt_template = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
                prompt_inputs = {k: inputs[k] for k in prompt_template.variable_keys if k in inputs}
                tmp_human_message = UserPromptMessage(content=prompt_template.format(prompt_inputs))

                rest_tokens = self._calculate_rest_token([tmp_human_message], model_config)

                histories = self._get_history_messages_from_memory(
                    memory=memory,
                    memory_config=memory_config,
                    max_token_limit=rest_tokens,
                    human_prefix=role_prefix.user,
                    ai_prefix=role_prefix.assistant,
                )
                prompt_inputs["#histories#"] = histories
            else:
                prompt_inputs["#histories#"] = ""

        return prompt_inputs
