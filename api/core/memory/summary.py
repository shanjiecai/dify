from langchain.memory import ConversationSummaryMemory

_DEFAULT_SUMMARIZER_TEMPLATE = """Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary.

EXAMPLE
Current summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.

New lines of conversation:
Human: Why do you think artificial intelligence is a force for good?
AI: Because artificial intelligence will help humans reach their full potential.

New summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF EXAMPLE

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""
from typing import Any

from langchain.chains.llm import LLMChain
from langchain.memory.chat_memory import BaseChatMemory
from langchain.memory.prompt import SUMMARY_PROMPT
from langchain.schema import (
    BaseChatMessageHistory,
    BasePromptTemplate,
)
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.messages import BaseMessage, ChatMessage, get_buffer_string
from pydantic import BaseModel, root_validator


class SummarizerMixin(BaseModel):
    """Mixin for summarizer."""

    human_prefix: str = "Human"
    ai_prefix: str = "AI"
    llm: BaseLanguageModel
    prompt: BasePromptTemplate = SUMMARY_PROMPT
    summary_message_cls: type[BaseMessage] = ChatMessage

    def predict_new_summary(
        self, messages: list[BaseMessage], existing_summary: str
    ) -> str:
        new_lines = get_buffer_string(
            messages,
            human_prefix=self.human_prefix,
            ai_prefix=self.ai_prefix,
        )

        chain = LLMChain(llm=self.llm, prompt=self.prompt)
        return chain.predict(summary=existing_summary, new_lines=new_lines)


class ConversationSummaryMemory(BaseChatMemory, SummarizerMixin):
    """Conversation summarizer to chat memory."""

    buffer: str = ""
    memory_key: str = "history"  #: :meta private:

    @classmethod
    def from_messages(
        cls,
        llm: BaseLanguageModel,
        chat_memory: BaseChatMessageHistory,
        *,
        summarize_step: int = 2,
        **kwargs: Any,
    ) -> ConversationSummaryMemory:
        obj = cls(llm=llm, chat_memory=chat_memory, **kwargs)
        for i in range(0, len(obj.chat_memory.messages), summarize_step):
            obj.buffer = obj.predict_new_summary(
                obj.chat_memory.messages[i : i + summarize_step], obj.buffer
            )
        return obj

    @property
    def memory_variables(self) -> list[str]:
        """Will always return list of memory variables.

        :meta private:
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Return history buffer."""
        if self.return_messages:
            buffer: Any = [self.summary_message_cls(content=self.buffer)]
        else:
            buffer = self.buffer
        return {self.memory_key: buffer}

    @root_validator()
    def validate_prompt_input_variables(cls, values: dict) -> dict:
        """Validate that prompt input variables are consistent."""
        prompt_variables = values["prompt"].input_variables
        expected_keys = {"summary", "new_lines"}
        if expected_keys != set(prompt_variables):
            raise ValueError(
                "Got unexpected prompt input variables. The prompt expects "
                f"{prompt_variables}, but it should have {expected_keys}."
            )
        return values

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """Save context from this conversation to buffer."""
        super().save_context(inputs, outputs)
        self.buffer = self.predict_new_summary(
            self.chat_memory.messages[-2:], self.buffer
        )

    def clear(self) -> None:
        """Clear memory contents."""
        super().clear()
        self.buffer = ""


