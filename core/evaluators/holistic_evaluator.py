from langchain_core.prompts import ChatPromptTemplate
from langchain_community.callbacks import get_openai_callback

from .base_evaluator import BaseEvaluator
from core.schemas.response_models import HolisticEvaluationResult


class HolisticEvaluator(BaseEvaluator):
    def evaluate(self, student_code: str, student_name: str, **kwargs) -> dict:
        system_msg = self.prompt_manager.read_prompt("legacy/evaluate_instructions.txt")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_msg),
                ("user", "Task: {task_description}\n\nStudent Code:\n{student_code}"),
            ]
        )

        structured_llm = self.llm.with_structured_output(HolisticEvaluationResult)
        chain = prompt | structured_llm

        with get_openai_callback() as cb:
            try:
                result: HolisticEvaluationResult = chain.invoke(
                    {
                        "student_code": student_code,
                        "task_description": self.task_description,
                    }
                )
                self.total_tokens += cb.total_tokens
                self.total_cost += cb.total_cost

                percentage = result.score
                score = round((percentage / 100.0) * 5.0, 1)
                return {
                    "student_name": student_name,
                    "success": True,
                    "score": float(score),
                    "percentage": int(percentage),
                    "evaluation": result.evaluation,
                    "eval_source": "Simple AI",
                }
            except Exception as e:
                return {"student_name": student_name, "success": False, "error": str(e)}
