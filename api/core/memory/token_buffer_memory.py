from typing import Optional

from core.file.message_file_parser import MessageFileParser
from core.model_manager import ModelInstance
from core.model_runtime.entities.message_entities import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    TextPromptMessageContent,
    UserPromptMessage,
)
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.model_providers import model_provider_factory
from extensions.ext_database import db
from models.model import Conversation, Message


class TokenBufferMemory:
    def __init__(self, conversation: Conversation, model_instance: ModelInstance) -> None:
        self.conversation = conversation
        self.model_instance = model_instance

    def get_history_prompt_messages(self, max_token_limit: int = 2000,
                                    message_limit: int = 10,
                                    assistant_name: Optional[str] = None,
                                    user_name: Optional[str] = None
                                    ) -> list[PromptMessage]:
        """
        Get history prompt messages.
        :param max_token_limit: max token limit
        :param message_limit: message limit
        :param assistant_name: assistant name
        :param user_name: user name
        """
        old_assistant_name = assistant_name
        old_user_name = user_name
        if not assistant_name:
            assistant_name = PromptMessageRole.USER.name
        if not user_name:
            user_name = PromptMessageRole.USER.name

        app_record = self.conversation.app

        # fetch limited messages, and return reversed
        messages = db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            # Message.answer != ''
        ).order_by(Message.created_at.desc()).limit(message_limit).all()

        messages = list(reversed(messages))
        message_file_parser = MessageFileParser(
            tenant_id=app_record.tenant_id,
            app_id=app_record.id
        )
        if messages[-1].answer is None or messages[-1].answer == "":
            # self.last_query = messages[-1].query
            # self.last_role = messages[-1].role
            messages = messages[:-1]

        prompt_messages = []
        for message in messages:
            if messages.index(message) + 1 < len(messages):
                next_message = messages[messages.index(message) + 1]
                # print(f"message: {message.answer}, next_message: {next_message.answer}")
                if (message.answer is None or message.answer == "") and message.query == next_message.query and \
                        message.role == next_message.role and next_message.answer is not None and \
                        next_message.answer != "":
                    continue
            files = message.message_files
            if files:
                file_objs = message_file_parser.transform_message_files(
                    files, message.app_model_config
                )

                if not file_objs:
                    prompt_messages.append(UserPromptMessage(content=message.query))
                else:
                    prompt_message_contents = [TextPromptMessageContent(data=message.query)]
                    for file_obj in file_objs:
                        prompt_message_contents.append(file_obj.prompt_message_content)

                    prompt_messages.append(UserPromptMessage(content=prompt_message_contents))
            else:
                if not old_user_name and (not old_assistant_name or old_assistant_name == "test"):
                    prompt_messages.append(UserPromptMessage(content=message.query))
                elif message.query:
                    prompt_messages.append(UserPromptMessage(content=message.query, role=user_name if (not message.role or message.role == "Human") else message.role))

            # prompt_messages.append(AssistantPromptMessage(content=message.answer))
            if (not old_assistant_name or old_assistant_name == "test") and not old_user_name:
                prompt_messages.append(AssistantPromptMessage(content=message.answer))
            elif message.answer:
                prompt_messages.append(UserPromptMessage(content=message.answer, role=assistant_name if not message.assistant_name else message.assistant_name))

        if not prompt_messages:
            return []

        # prune the chat message if it exceeds the max token limit
        provider_instance = model_provider_factory.get_provider_instance(self.model_instance.provider)
        model_type_instance = provider_instance.get_model_instance(ModelType.LLM)

        curr_message_tokens = model_type_instance.get_num_tokens(
            self.model_instance.model,
            self.model_instance.credentials,
            prompt_messages
        )

        if curr_message_tokens > max_token_limit:
            pruned_memory = []
            while curr_message_tokens > max_token_limit and prompt_messages:
                pruned_memory.append(prompt_messages.pop(0))
                curr_message_tokens = model_type_instance.get_num_tokens(
                    self.model_instance.model,
                    self.model_instance.credentials,
                    prompt_messages
                )

        return prompt_messages

    def get_history_prompt_text(self, human_prefix: str = "Human",
                                ai_prefix: str = "Assistant",
                                max_token_limit: int = 2000,
                                message_limit: int = 10) -> str:
        """
        Get history prompt text.
        :param human_prefix: human prefix
        :param ai_prefix: ai prefix
        :param max_token_limit: max token limit
        :param message_limit: message limit
        :return:
        """
        prompt_messages = self.get_history_prompt_messages(
            max_token_limit=max_token_limit,
            message_limit=message_limit
        )

        string_messages = []
        for m in prompt_messages:
            if m.role == PromptMessageRole.USER:
                role = human_prefix
            elif m.role == PromptMessageRole.ASSISTANT:
                role = ai_prefix
            else:
                if m.role:
                    role = m.role
                else:
                    continue

            message = f"{role}: {m.content}"
            string_messages.append(message)

        return "\n".join(string_messages)