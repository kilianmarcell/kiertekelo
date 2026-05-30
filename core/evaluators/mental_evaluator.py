import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.callbacks import get_openai_callback

from .base_evaluator import BaseEvaluator


class MentalEvaluator(BaseEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_test_cases = None

    def generate_mental_test_cases(self) -> dict:
        if self._cached_test_cases is not None:
            return self._cached_test_cases

        system_msg = self.prompt_manager.read_prompt(
            "mental/mental_test_gen_instructions.txt"
        )
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
            self._cached_test_cases = json.loads(clean_content)
            return self._cached_test_cases
        except Exception as e:
            print(f"Error generating mental test cases: {e}")
            self._cached_test_cases = {"test_cases": []}
            return self._cached_test_cases

    def evaluate(self, student_code: str, student_name: str, **kwargs) -> dict:
        mental_test_cases = self.generate_mental_test_cases()

        system_msg_template = self.prompt_manager.read_prompt(
            "mental/mental_execution_instructions.txt"
        )
        system_msg = system_msg_template.replace(
            "__TASK__", self.task_description
        ).replace("__TEST_CASES__", json.dumps(mental_test_cases, indent=2))

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Student Code:\n{student_code}"),
        ]

        with get_openai_callback() as cb:
            try:
                response = self.llm.invoke(messages)
                self.total_tokens += cb.total_tokens
                self.total_cost += cb.total_cost

                content = response.content
                match = re.search(r"FINAL_PERCENTAGE:\s*(\d+)", content)
                percentage = int(match.group(1)) if match else 0
                score = round((percentage / 100.0) * 5.0, 1)

                return {
                    "student_name": student_name,
                    "success": True,
                    "score": float(score),
                    "percentage": int(percentage),
                    "evaluation": content[:500] + "...",
                    "test_results": [],
                    "eval_source": "Mental Execution (Relaxed)",
                }
            except Exception as e:
                return {"student_name": student_name, "success": False, "error": str(e)}
