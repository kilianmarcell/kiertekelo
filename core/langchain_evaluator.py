import os
import json
import re
from typing import Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.callbacks import get_openai_callback

from settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    MODEL,
    MODEL_MINI,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
)
from .schemas.response_models import TestScriptSchema

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROMPTS_DIR = os.path.join(_ROOT_DIR, "prompts")
_SCHEMA_PARTS_DIR = os.path.join(_PROMPTS_DIR, "schema_parts")
_TEST_GEN_PARTS_DIR = os.path.join(_PROMPTS_DIR, "test_gen_parts")
_TESTER_TEMPLATES_DIR = os.path.join(_PROMPTS_DIR, "tester_templates")
_COMMON_PROMPTS_DIR = os.path.join(_PROMPTS_DIR, "common")


from .mixins.evaluator_utils import EvaluatorUtilsMixin
from .mixins.evaluator_schema import SchemaGeneratorMixin
from .mixins.evaluator_mental import MentalExecutionMixin
from .mixins.evaluator_legacy import LegacyExecutionMixin


class LangChainCodeEvaluator(
    EvaluatorUtilsMixin,
    SchemaGeneratorMixin,
    MentalExecutionMixin,
    LegacyExecutionMixin,
):
    def __init__(
        self,
        api_key: str = OPENROUTER_API_KEY,
        task_description: Optional[str] = None,
        model: str = MODEL,
        model_mini: str = MODEL_MINI,
    ):
        self.api_key = api_key
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model_kwargs={"top_p": LLM_TOP_P},
        )
        self.llm_mini = ChatOpenAI(
            model=model_mini,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=0,
            model_kwargs={"top_p": LLM_TOP_P},
        )
        self.task_description = task_description or self._load_task_description()
        self.grading_schema: Optional[Dict] = None
        self.total_tokens = 0
        self.total_cost = 0
