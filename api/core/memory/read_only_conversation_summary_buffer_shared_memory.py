from __future__ import annotations

import datetime
from typing import Any, List, Dict

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import get_buffer_string, BaseMessage, ChatMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory.summary import SummarizerMixin
from pydantic import root_validator

from core.model_providers.models.entity.message import PromptMessage, MessageType, to_lc_messages
from core.model_providers.models.llm.base import BaseLLM
from extensions.ext_database import db
from models.model import Conversation, Message


class ReadOnlyConversationSummaryBufferSharedMemory(BaseChatMemory, SummarizerMixin):
    """Buffer with summarizer for storing conversation memory."""

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
    messages:List[Message] = None

    @property
    def buffer(self) -> List[BaseMessage]:
        """String buffer of memory."""
        # fetch limited messages desc, and return reversed
        messages = db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.updated_at > self.previous_summary_updated_at,
            # Message.answer_tokens > 0
        ).order_by(Message.created_at.desc()).limit(self.message_limit).all()

        messages = list(reversed(messages))
        self.messages = messages

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
        previous_summary: str = self.conversation.previous_summary
        if not previous_summary:
            previous_summary = ""
            self.previous_summary_updated_at = datetime.datetime(1970, 1, 1)
        else:
            self.previous_summary_updated_at = self.conversation.previous_summary_updated_at
        print(f"max_token_limit: {self.max_token_limit}")

        buffer = self.buffer
        self.moving_summary_buffer = previous_summary
        self.prune()

        # self.predict_new_summary(buffer, self.moving_summary_buffer)
        if self.moving_summary_buffer != "":
            buffer = self.buffer
            first_messages: List[BaseMessage] = [
                self.summary_message_cls(content=self.moving_summary_buffer)
            ]
            buffer = first_messages + buffer
        if self.return_messages:
            final_buffer: Any = buffer
        else:
            final_buffer = get_buffer_string(
                buffer, human_prefix=self.human_prefix, ai_prefix=self.ai_prefix
            )
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
        super().save_context(inputs, outputs)
        self.prune()

    def prune(self) -> None:
        """Prune buffer if it exceeds max token limit"""
        buffer = self.chat_memory.messages
        curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
        if curr_buffer_length > self.max_token_limit:
            pruned_memory = []
            while curr_buffer_length + len(self.moving_summary_buffer) > self.max_token_limit and buffer:
                pruned_memory.append(buffer.pop(0))
                curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
            self.moving_summary_buffer = self.predict_new_summary(
                pruned_memory, self.moving_summary_buffer
            )
            self.buffer = pruned_memory
            print(f"Pruned memory: {pruned_memory}")
            print(f"New summary: {self.moving_summary_buffer}")
            self.conversation.previous_summary = self.moving_summary_buffer
            self.conversation.previous_summary_updated_at = self.messages[-1].updated_at
            db.session.add(self.conversation)
            db.session.commit()

    def clear(self) -> None:
        """Nothing to clear, got a memory like a vault."""
        super().clear()
        self.moving_summary_buffer = ""
