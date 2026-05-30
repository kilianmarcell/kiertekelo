from typing import Optional, Dict
from pathlib import Path

from settings import (
    OPENROUTER_API_KEY,
    MODEL,
    MODEL_MINI,
)
from core.utils.helpers import load_task_description, detect_language
from core.evaluators.holistic_evaluator import HolisticEvaluator
from core.evaluators.mental_evaluator import MentalEvaluator
from core.evaluators.testcase_evaluator import TestcaseEvaluator


class LangChainCodeEvaluator:
    def __init__(
        self,
        api_key: str = OPENROUTER_API_KEY,
        task_description: Optional[str] = None,
        model: str = MODEL,
        model_mini: str = MODEL_MINI,
    ):
        root_dir = Path(__file__).resolve().parent.parent

        self.api_key = api_key
        self.task_description = task_description or load_task_description(root_dir)

        self.holistic_eval = HolisticEvaluator(
            api_key, self.task_description, model, model_mini
        )
        self.mental_eval = MentalEvaluator(
            api_key, self.task_description, model, model_mini
        )
        self.testcase_eval = TestcaseEvaluator(
            api_key, self.task_description, model, model_mini
        )

    @property
    def total_tokens(self) -> int:
        return (
            self.holistic_eval.total_tokens
            + self.mental_eval.total_tokens
            + self.testcase_eval.total_tokens
        )

    @property
    def total_cost(self) -> float:
        return (
            self.holistic_eval.total_cost
            + self.mental_eval.total_cost
            + self.testcase_eval.total_cost
        )

    def evaluate(
        self,
        student_code: str,
        student_name: str,
        evaluation_mode: str = "original",
        **kwargs
    ) -> dict:
        if evaluation_mode == "mental":
            return self.mental_eval.evaluate(student_code, student_name, **kwargs)
        elif evaluation_mode == "testcases":
            return self.testcase_eval.evaluate(student_code, student_name, **kwargs)
        else:
            return self.holistic_eval.evaluate(student_code, student_name, **kwargs)

    def generate_grading_schema(self) -> Dict:
        return self.testcase_eval.generate_grading_schema()

    def generate_shared_test_script(self, language: str = "java") -> str:
        return self.testcase_eval.generate_shared_test_script(language)

    def evaluate_standalone(
        self,
        student_code: str,
        student_name: str,
        shared_test_script: Optional[str],
        language: str = "java",
    ) -> dict:
        return self.testcase_eval.evaluate(
            student_code,
            student_name,
            shared_test_script=shared_test_script,
            language=language,
        )

    def detect_language(self, content: str = "", filename: str = "") -> str:
        return detect_language(content, filename)
