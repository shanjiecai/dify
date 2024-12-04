import datetime
from collections.abc import Sequence
from typing import Optional

from core.app.entities.app_invoke_entities import ModelConfigWithCredentialsEntity
from core.file import file_manager
from core.file.models import File
from core.helper.code_executor.jinja2.jinja2_formatter import Jinja2Formatter
from core.helper.openai_name_convert import correct_name_field
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_runtime.entities import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContent,
    PromptMessageRole,
    SystemPromptMessage,
    TextPromptMessageContent,
    UserPromptMessage,
)
from core.model_runtime.entities.message_entities import ImagePromptMessageContent
from core.prompt.entities.advanced_prompt_entities import ChatModelMessage, CompletionModelPromptTemplate, MemoryConfig
from core.prompt.prompt_transform import PromptTransform
from core.prompt.utils.prompt_template_parser import PromptTemplateParser
from core.prompt_const import plan_question_template
from core.workflow.entities.variable_pool import VariablePool
from models.model import Conversation
from mylogger import logger


class AdvancedPromptTransform(PromptTransform):
    """
    Advanced Prompt Transform for Workflow LLM Node.
    """

    def __init__(
        self,
        with_variable_tmpl: bool = False,
        image_detail_config: ImagePromptMessageContent.DETAIL = ImagePromptMessageContent.DETAIL.LOW,
    ) -> None:
        self.with_variable_tmpl = with_variable_tmpl
        self.image_detail_config = image_detail_config

    def get_prompt(
        self,
        *,
        prompt_template: Sequence[ChatModelMessage] | CompletionModelPromptTemplate,
        inputs: dict[str, str],
        query: str,
        files: Sequence[File],
        context: Optional[str],
        memory_config: Optional[MemoryConfig],
        memory: Optional[TokenBufferMemory],
            model_config: ModelConfigWithCredentialsEntity,
            assistant_name: Optional[str] = None,
            user_name: Optional[str] = None,
            conversation: Conversation = None,
            query_prompt_template: Optional[str] = None,
    ) -> list[PromptMessage]:
        prompt_messages = []

        if isinstance(prompt_template, CompletionModelPromptTemplate):
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
        elif isinstance(prompt_template, list) and all(isinstance(item, ChatModelMessage) for item in prompt_template):
            prompt_messages = self._get_chat_model_prompt_messages(
                prompt_template=prompt_template,
                inputs=inputs,
                query=query,
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
        files: Sequence[File],
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
            parser = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
            prompt_inputs = {k: inputs[k] for k in parser.variable_keys if k in inputs}

            prompt_inputs = self._set_context_variable(context, parser, prompt_inputs)

            if memory and memory_config:
                role_prefix = memory_config.role_prefix
                prompt_inputs = self._set_histories_variable(
                    memory=memory,
                    memory_config=memory_config,
                    raw_prompt=raw_prompt,
                    role_prefix=role_prefix,
                    parser=parser,
                    prompt_inputs=prompt_inputs,
                    model_config=model_config,
                )

            if query:
                prompt_inputs = self._set_query_variable(query, parser, prompt_inputs)

            prompt = parser.format(prompt_inputs)
        else:
            prompt = raw_prompt
            prompt_inputs = inputs

            prompt = Jinja2Formatter.format(prompt, prompt_inputs)

        if files:
            prompt_message_contents: list[PromptMessageContent] = []
            prompt_message_contents.append(TextPromptMessageContent(data=prompt))
            for file in files:
                prompt_message_contents.append(file_manager.to_prompt_message_content(file))

            prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
        else:
            prompt_messages.append(UserPromptMessage(content=prompt))

        return prompt_messages

    def _get_chat_model_prompt_messages(
        self,
        prompt_template: list[ChatModelMessage],
        inputs: dict,
        query: Optional[str],
        files: Sequence[File],
        context: Optional[str],
        memory_config: Optional[MemoryConfig],
        memory: Optional[TokenBufferMemory],
        model_config: ModelConfigWithCredentialsEntity,
        assistant_name: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation: Conversation = None,
    ) -> list[PromptMessage]:
        """
        Get chat model prompt messages.
        """
        prompt_messages = []
        for prompt_item in prompt_template:
            raw_prompt = prompt_item.text

            if prompt_item.edition_type == "basic" or not prompt_item.edition_type:
                if self.with_variable_tmpl:
                    vp = VariablePool()
                    for k, v in inputs.items():
                        if k.startswith("#"):
                            vp.add(k[1:-1].split("."), v)
                    raw_prompt = raw_prompt.replace("{{#context#}}", context or "")
                    prompt = vp.convert_template(raw_prompt).text
                else:
                    parser = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
                    prompt_inputs = {k: inputs[k] for k in parser.variable_keys if k in inputs}
                    prompt_inputs = self._set_context_variable(
                        context=context, parser=parser, prompt_inputs=prompt_inputs
                    )
                    prompt = parser.format(prompt_inputs)
            elif prompt_item.edition_type == "jinja2":
                prompt = raw_prompt
                prompt_inputs = inputs
                prompt = Jinja2Formatter.format(template=prompt, inputs=prompt_inputs)
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

        if query and memory_config and memory_config.query_prompt_template:
            parser = PromptTemplateParser(
                template=memory_config.query_prompt_template, with_variable_tmpl=self.with_variable_tmpl
            )
            prompt_inputs = {k: inputs[k] for k in parser.variable_keys if k in inputs}
            prompt_inputs["#sys.query#"] = query

            prompt_inputs = self._set_context_variable(context, parser, prompt_inputs)

            query = parser.format(prompt_inputs)

        if memory and memory_config:
            if conversation and conversation.plan_question:
                # 历史只取十轮
                prompt_messages = self._append_chat_histories(
                    memory, memory_config, prompt_messages, model_config, message_limit=10
                )
            else:
                prompt_messages = self._append_chat_histories(memory, memory_config, prompt_messages, model_config)

            if files and query is not None:
                prompt_message_contents: list[PromptMessageContent] = []
                prompt_message_contents.append(TextPromptMessageContent(data=query))
                for file in files:
                    prompt_message_contents.append(file_manager.to_prompt_message_content(file))
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
                        prompt_message_contents.append(file_manager.to_prompt_message_content(file))

                    last_message.content = prompt_message_contents
                else:
                    prompt_message_contents = [TextPromptMessageContent(data="")]  # not for query
                    for file in files:
                        prompt_message_contents.append(file_manager.to_prompt_message_content(file))

                    prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
            else:
                prompt_message_contents = [TextPromptMessageContent(data=query)]
                for file in files:
                    prompt_message_contents.append(file_manager.to_prompt_message_content(file))

                prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
        elif query:
            if user_name:
                prompt_messages.append(UserPromptMessage(content=query, name=correct_name_field(user_name)))
            else:
                prompt_messages.append(UserPromptMessage(content=query))

        return prompt_messages

    def _set_context_variable(self, context: str | None, parser: PromptTemplateParser, prompt_inputs: dict) -> dict:
        if "#context#" in parser.variable_keys:
            if context:
                prompt_inputs["#context#"] = context
            else:
                prompt_inputs["#context#"] = ""

        return prompt_inputs

    def _set_query_variable(self, query: str, parser: PromptTemplateParser, prompt_inputs: dict) -> dict:
        if "#query#" in parser.variable_keys:
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
        parser: PromptTemplateParser,
        prompt_inputs: dict,
        model_config: ModelConfigWithCredentialsEntity,
    ) -> dict:
        if "#histories#" in parser.variable_keys:
            if memory:
                inputs = {"#histories#": "", **prompt_inputs}
                parser = PromptTemplateParser(template=raw_prompt, with_variable_tmpl=self.with_variable_tmpl)
                prompt_inputs = {k: inputs[k] for k in parser.variable_keys if k in inputs}
                tmp_human_message = UserPromptMessage(content=parser.format(prompt_inputs))

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
