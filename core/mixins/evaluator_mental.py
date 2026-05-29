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
from ..schemas.response_models import TestScriptSchema

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PROMPTS_DIR = os.path.join(_ROOT_DIR, "prompts")
_SCHEMA_PARTS_DIR = os.path.join(_PROMPTS_DIR, "schema_parts")
_TEST_GEN_PARTS_DIR = os.path.join(_PROMPTS_DIR, "test_gen_parts")
_TESTER_TEMPLATES_DIR = os.path.join(_PROMPTS_DIR, "tester_templates")
_COMMON_PROMPTS_DIR = os.path.join(_PROMPTS_DIR, "common")


class MentalExecutionMixin:
    def generate_mental_test_cases(self) -> dict:
        """Generate a list of mental test cases for the task."""
        path = os.path.join(_PROMPTS_DIR, "mental", "mental_test_gen_instructions.txt")
        system_msg = self._read_prompt_file(path)

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Task: {self.task_description}"),
        ]

        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            self.total_tokens += cb.total_tokens
            self.total_cost += cb.total_cost

        try:
            clean_content = (
                response.content.replace("```json", "").replace("```", "").strip()
            )
            return json.loads(clean_content)
        except Exception as e:
            print(f"Error generating mental test cases: {e}")
            return {"test_cases": []}

    def evaluate_mental_execution(
        self, student_code: str, student_name: str, mental_test_cases: dict
    ) -> dict:
        """Evaluate student code by mentally executing test cases."""
        path = os.path.join(_PROMPTS_DIR, "mental", "mental_execution_instructions.txt")
        system_msg = (
            self._read_prompt_file(path)
            .replace("__TASK__", self.task_description)
            .replace("__TEST_CASES__", json.dumps(mental_test_cases, indent=2))
        )

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Student Code:\n{student_code}"),
        ]

        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            self.total_tokens += cb.total_tokens
            self.total_cost += cb.total_cost

        try:
            content = response.content
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                clean_content = json_match.group(1)
            else:
                clean_content = (
                    content.replace("```json", "").replace("```", "").strip()
                )

            res = json.loads(clean_content)
            percentage = res.get("final_percentage", 0)
            score = round((percentage / 100.0) * 5.0, 1)

            return {
                "student_name": student_name,
                "success": True,
                "score": float(score),
                "percentage": int(percentage),
                "evaluation": res.get("overall_evaluation", ""),
                "test_results": res.get("test_results", []),
                "eval_source": "Mental Execution",
            }
        except Exception as e:
            return {"student_name": student_name, "success": False, "error": str(e)}
