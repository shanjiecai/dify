from __future__ import annotations

import datetime
from typing import Any, List, Dict

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import get_buffer_string, BaseMessage, ChatMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory.summary import SummarizerMixin
# from .summary import SummarizerMixin
from langchain.schema.language_model import BaseLanguageModel
from pydantic import root_validator

from controllers.service_api.app import create_or_update_end_user_for_user_id
from core.model_providers.models.entity.message import PromptMessage, MessageType, to_lc_messages, to_prompt_messages
from core.model_providers.models.llm.base import BaseLLM
from core.prompt.prompt_builder import PromptBuilder
from extensions.ext_database import db
from models.model import Conversation, Message, App


class ReadOnlyConversationSummaryBufferSharedMemory(BaseChatMemory, SummarizerMixin):
    """Buffer with summarizer for storing conversation memory."""

    llm: BaseLanguageModel  # openai model
    conversation: Conversation
    human_prefix: str = "Human"
    ai_prefix: str = "Assistant"
    model_instance: BaseLLM
    memory_key: str = "chat_history"
    max_token_limit: int = 2000
    message_limit: int = 20
    moving_summary_buffer: str = ""
    # 默认1970年
    previous_summary_updated_at: datetime.datetime = datetime.datetime(1970, 1, 1)
    messages: List[Message] = None
    final_buffer: str|None = None

    @property
    def buffer(self) -> List[BaseMessage]:
        """String buffer of memory."""
        # fetch limited messages desc, and return reversed
        print(f"conversation: {self.conversation.previous_summary_updated_at}")
        if not self.conversation.previous_summary_updated_at:
            # 1970年
            self.conversation.previous_summary_updated_at = datetime.datetime(1970, 1, 1)
        messages = db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.updated_at > self.conversation.previous_summary_updated_at,
            # Message.answer_tokens > 0
        ).order_by(Message.created_at.desc()).limit(self.message_limit).all()

        messages = list(reversed(messages))

        print(f"messages: {messages[-1].updated_at}")
        self.messages = messages.copy()

        chat_messages: List[PromptMessage|ChatMessage] = []
        for message in messages[:-1]:
            if message.role == "Human":
                chat_messages.append(PromptMessage(content=message.query, type=MessageType.USER))
            else:
                chat_messages.append(ChatMessage(content=message.query, role=message.role, type=message.role))
            if message.answer:
                if self.ai_prefix == "Assistant":
                    chat_messages.append(PromptMessage(content=message.answer, type=MessageType.ASSISTANT))
                else:
                    chat_messages.append(ChatMessage(content=message.answer, role=self.ai_prefix, type=self.ai_prefix))

        if not chat_messages:
            return []

        # prune the chat message if it exceeds the max token limit
        # curr_buffer_length = self.model_instance.get_num_tokens(chat_messages)
        # if curr_buffer_length > self.max_token_limit:
        #     pruned_memory = []
        #     while curr_buffer_length > self.max_token_limit and chat_messages:
        #         pruned_memory.append(chat_messages.pop(0))
        #         curr_buffer_length = self.model_instance.get_num_tokens(chat_messages)
        self.chat_memory.messages = chat_messages
        return to_lc_messages(chat_messages)

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables.

        :meta private:
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return history buffer."""
        if self.final_buffer:
            return {self.memory_key: self.final_buffer}
        buffer = self.buffer
        self.prune()

        # previous_summary: str = self.conversation.previous_summary
        # if not previous_summary:
        #     previous_summary = ""
        #     self.previous_summary_updated_at = datetime.datetime(1970, 1, 1)
        # else:
        #     self.previous_summary_updated_at = self.conversation.previous_summary_updated_at
        # print(f"max_token_limit: {self.max_token_limit}")
        # self.moving_summary_buffer = previous_summary

        # self.predict_new_summary(buffer, self.moving_summary_buffer)
        if self.moving_summary_buffer != "":
            # buffer = self.buffer
            first_messages: List[BaseMessage] = [
                # self.summary_message_cls(content=self.moving_summary_buffer, role="Previous conversation", type="Previous conversation")
                self.summary_message_cls(content=self.moving_summary_buffer)
            ]
            buffer = first_messages + buffer
        if self.return_messages:
            final_buffer: Any = buffer
        else:
            final_buffer = get_buffer_string(
                buffer, human_prefix=self.human_prefix, ai_prefix=self.ai_prefix
            )
        self.conversation.previous_summary = self.moving_summary_buffer
        self.conversation.previous_summary_updated_at = self.messages[-1].updated_at
        db.session.add(self.conversation)
        db.session.commit()
        print(f"final_buffer: {final_buffer}")
        self.final_buffer = final_buffer
        return {self.memory_key: final_buffer}

    @root_validator()
    def validate_prompt_input_variables(cls, values: Dict) -> Dict:
        """Validate that prompt input variables are consistent."""
        prompt_variables = values["prompt"].input_variables
        expected_keys = {"summary", "new_lines"}
        if expected_keys != set(prompt_variables):
            raise ValueError(
                "Got unexpected prompt input variables. The prompt expects "
                f"{prompt_variables}, but it should have {expected_keys}."
            )
        return values

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Nothing should be saved or changed"""
        # super().save_context(inputs, outputs)
        # self.prune()
        pass

    def prune(self) -> None:
        """Prune buffer if it exceeds max token limit"""
        print("init prune")
        buffer = self.chat_memory.messages
        curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
        previous_summary_length = self.llm.get_num_tokens(str(self.conversation.previous_summary))
        if curr_buffer_length + previous_summary_length > self.max_token_limit:
            print("start pruning memory")
            # pruned_memory = []
            # while curr_buffer_length + len(self.moving_summary_buffer) > self.max_token_limit and buffer:
            #     pruned_memory.append(buffer.pop(0))
            #     curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
            self.moving_summary_buffer = self.predict_new_summary(
                buffer, self.conversation.previous_summary
            )
            self.chat_memory.messages = buffer
            print(f"Pruned memory: {buffer}")
            print(f"New summary: {self.moving_summary_buffer}")

    def clear(self) -> None:
        """Nothing to clear, got a memory like a vault."""
        super().clear()
        self.moving_summary_buffer = ""


if __name__ == "__main__":
    from core.model_providers.model_factory import ModelFactory

    app = db.session.query(App).filter(App.id == "ba0dd05e-c088-4cd0-b9ae-ddb55fcc5a46").first()
    app_model_config = app.app_model_config.copy()
    model_dict = app_model_config.model_dict
    memory_model_instance = ModelFactory.get_text_generation_model_from_model_config(
        tenant_id=app.tenant_id,
        model_config=app_model_config.model_dict
    )
    system_message = PromptBuilder.to_system_message(app_model_config.pre_prompt, {})
    system_instruction = system_message.content
    # model_instance = ModelFactory.get_text_generation_model(
    #     tenant_id=app.tenant_id,
    #     model_provider_name=model_dict.get('provider'),
    #     model_name=model_dict.get('name')
    # )
    system_instruction_tokens = memory_model_instance.get_num_tokens(to_prompt_messages([system_message]))

    from langchain.llms import OpenAI
    llm = OpenAI(openai_api_key=memory_model_instance.credentials["openai_api_key"])
    end_user = create_or_update_end_user_for_user_id(app, "")
    conversation = Conversation(
        app_id=app.id,
        app_model_config_id=app_model_config.id,
        model_provider=model_dict.get('provider'),
        model_id=model_dict.get('name'),
        override_model_configs=None,
        mode=app.mode,
        name='',
        inputs={},
        introduction=app_model_config.opening_statement,
        system_instruction=system_instruction,
        system_instruction_tokens=system_instruction_tokens,
        status='normal',
        from_source='api',
        from_end_user_id=end_user.id,
        from_account_id=None,
    )

    memory = ReadOnlyConversationSummaryBufferSharedMemory(
        llm=llm,
        conversation=conversation,
        model_instance=memory_model_instance,
        max_token_limit=100,
        memory_key="chat_history",
        return_messages=True,
        input_key="input",
        output_key="output",
        message_limit=100,
        human_prefix="Human",
        ai_prefix="Reagan Ericson",
        moving_summary_buffer="",
        vebrose=True
    )
    print(memory.load_memory_variables({}))
