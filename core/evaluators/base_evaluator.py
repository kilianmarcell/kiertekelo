from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from core.utils.prompt_manager import PromptManager
from settings import (
    MODEL,
    MODEL_MINI,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
    OPENROUTER_BASE_URL,
)


class BaseEvaluator(ABC):
    def __init__(
        self,
        api_key: str,
        task_description: str,
        model: str = MODEL,
        model_mini: str = MODEL_MINI,
    ):
        self.api_key = api_key
        self.task_description = task_description
        self.prompt_manager = PromptManager()

        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            top_p=LLM_TOP_P,
        )
        self.llm_mini = ChatOpenAI(
            model=model_mini,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=0,
            top_p=LLM_TOP_P,
        )

        self.total_tokens = 0
        self.total_cost = 0

    @abstractmethod
    def evaluate(self, student_code: str, student_name: str, **kwargs) -> dict:
        pass
