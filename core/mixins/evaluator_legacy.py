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


class LegacyExecutionMixin:
    def evaluate(
        self, student_code: str, student_name: str, evaluation_mode: str = "original"
    ) -> dict:
        role_path = os.path.join(_PROMPTS_DIR, "legacy", "evaluate_instructions.txt")
        system_msg = self._read_prompt_file(role_path)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_msg),
                ("user", "Task: {task_description}\n\nStudent Code:\n{student_code}"),
            ]
        )

        chain = prompt | self.llm

        with get_openai_callback() as cb:
            response = chain.invoke(
                {
                    "student_code": student_code,
                    "task_description": self.task_description,
                }
            )
            self.total_tokens += cb.total_tokens
            self.total_cost += cb.total_cost

        try:
            clean_content = (
                response.content.replace("```json", "").replace("```", "").strip()
            )
            res = json.loads(clean_content)
            percentage = res.get("score", 0)
            score = round((percentage / 100.0) * 5.0, 1)
            return {
                "student_name": student_name,
                "success": True,
                "score": float(score),
                "percentage": int(percentage),
                "evaluation": res.get("evaluation", ""),
                "eval_source": "Simple AI",
            }
        except Exception as e:
            return {"student_name": student_name, "success": False, "error": str(e)}

    def evaluate_standalone(
        self,
        student_code: str,
        student_name: str,
        shared_test_script: Optional[str],
        language: str = "java",
    ) -> dict:
        from ..tools.java_executor import run_java_test_script
        from ..tools.python_executor import run_python_test_script
        from ..tools.cpp_executor import run_cpp_test_script

        passed_raw = 0
        total_raw = 100
        execution_valid = False

        if shared_test_script:
            if language == "java":
                res = run_java_test_script.invoke(
                    {"script_content": shared_test_script, "student_code": student_code}
                )
            elif language == "cpp":
                res_raw = run_cpp_test_script.invoke(
                    {"script_content": shared_test_script, "student_code": student_code}
                )
                res = {"output": res_raw}
            else:
                full = student_code + "\n\n" + shared_test_script
                raw = run_python_test_script.invoke({"script_content": full})
                res = {"output": raw}

            output = res.get("output", "")
            match = re.search(r"TOTAL_SCORE:\s*(\d+)", output, re.IGNORECASE)
            if match:
                passed_raw = int(match.group(1))
                execution_valid = True

        if not execution_valid or passed_raw < total_raw:
            eval_source = "Smart Static (GPT-4o-mini)"
            smart_pts = self._evaluate_statically_internal(student_code)

            if execution_valid:
                exec_pts = (passed_raw / total_raw) * 100
                final_percentage = max(exec_pts, smart_pts)
            else:
                final_percentage = smart_pts
        else:
            final_percentage = 100
            eval_source = "Dynamic (Execution)"

        final_percentage = min(100, final_percentage)
        final_score = round((final_percentage / 100.0) * 5.0, 1)
        final_score = min(5.0, final_score)

        return {
            "student_name": student_name,
            "success": True,
            "score": float(final_score),
            "percentage": int(final_percentage),
            "evaluation": f"Evaluation via {eval_source}.",
            "eval_source": eval_source,
        }

    def _evaluate_statically_internal(self, code: str) -> int:
        if not self.grading_schema:
            self.generate_grading_schema()

        path = os.path.join(_PROMPTS_DIR, "legacy", "fallback_instructions.txt")
        system_msg = (
            self._read_prompt_file(path)
            .replace("__SCHEMA__", json.dumps(self.grading_schema))
            .replace("__TASK__", self.task_description)
        )

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Code to evaluate:\n{code}"),
        ]

        try:
            with get_openai_callback() as cb:
                response = self.llm_mini.invoke(messages)
                self.total_tokens += cb.total_tokens
                self.total_cost += cb.total_cost

            content = response.content
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                clean_content = json_match.group(1)
            else:
                clean_content = (
                    content.replace("```json", "").replace("```", "").strip()
                )

            res = json.loads(clean_content)

            weighted_total = 0
            for cat in self.grading_schema["categories"]:
                cat_id = cat["id"]
                score = 0
                for s in res.get("category_scores", []):
                    if str(s.get("id")) == str(cat_id):
                        score = s.get("score_percentage", 0)
                        break
                weighted_total += (score / 100.0) * cat["weight"]

            return int(weighted_total)
        except Exception as e:
            print(f"Smart fallback error: {e}")
            return 0
