import json
import re
import ast
from typing import Optional, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.callbacks import get_openai_callback

from .base_evaluator import BaseEvaluator
from core.schemas.response_models import TestScriptSchema
from core.schemas.fallback_schema import get_fallback_grading_schema
from core.utils.helpers import extract_class_name_from_task


class TestcaseEvaluator(BaseEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grading_schema: Optional[Dict] = None

    def generate_grading_schema(self) -> Dict:
        class_name = extract_class_name_from_task(self.task_description)
        system_msg = self.prompt_manager.build_system_msg_from_schema_parts()

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Task: {self.task_description}"),
        ]

        with get_openai_callback() as cb:
            response = self.llm.invoke(messages)
            self.total_tokens += cb.total_tokens
            self.total_cost += cb.total_cost

        clean_content = (
            response.content.replace("```json", "").replace("```", "").strip()
        )
        try:
            self.grading_schema = json.loads(clean_content)
        except:
            self.grading_schema = get_fallback_grading_schema(class_name)
        return self.grading_schema

    def generate_shared_test_script(self, language: str = "java") -> str:
        class_name = extract_class_name_from_task(self.task_description)
        parser = PydanticOutputParser(pydantic_object=TestScriptSchema)

        try:
            parts = [
                self.prompt_manager.read_prompt("common/role.txt"),
                self.prompt_manager.read_prompt("test_gen_parts/01_goal.txt"),
                self.prompt_manager.read_prompt(f"test_gen_parts/02_{language}.txt"),
                self.prompt_manager.read_prompt("test_gen_parts/03_footer.txt"),
            ]
            system_msg = "\n\n".join(parts)
            system_msg = system_msg.replace("__CLASS_NAME__", class_name).replace(
                "__LANGUAGE__", language
            )
        except Exception as e:
            raise RuntimeError(f"Error building test generation prompt: {e}")

        system_msg += "\n\n" + parser.get_format_instructions()
        safe_system_msg = system_msg.replace("{", "{{").replace("}", "}}")
        prompt = ChatPromptTemplate.from_messages(
            [("system", safe_system_msg), ("user", "Task: {task_description}")]
        )

        chain = prompt | self.llm
        with get_openai_callback() as cb:
            response = chain.invoke({"task_description": self.task_description})
            self.total_tokens += cb.total_tokens
            self.total_cost += cb.total_cost

        try:
            structured_data = parser.parse(response.content)
            return self._build_script_from_schema(structured_data, language, class_name)
        except Exception as e:
            print(f"Error parsing structured test script: {e}")
        return ""

    def _build_script_from_schema(
        self, schema: TestScriptSchema, language: str, class_name: str
    ) -> str:
        test_calls = []
        is_java = language == "java"

        for tc in schema.test_cases:
            if is_java:
                line = (
                    '        runTest("'
                    + tc.name
                    + '", '
                    + str(tc.weight)
                    + ", () -> { "
                    + tc.logic
                    + " });"
                )
            else:
                line = (
                    '        RUN_TEST("'
                    + tc.name
                    + '", '
                    + str(tc.weight)
                    + ", "
                    + tc.logic
                    + ");"
                )
            test_calls.append(line)

        body_str = "\n".join(test_calls)
        template = self.prompt_manager.read_prompt(
            f"tester_templates/{language}_template.txt"
        )

        if template:
            return template.replace("__CLASS_NAME__", class_name).replace(
                "__BODY__", body_str
            )

        return ""

    def evaluate(self, student_code: str, student_name: str, **kwargs) -> dict:
        shared_test_script = kwargs.get("shared_test_script")
        language = kwargs.get("language", "java")
        return self._evaluate_standalone(
            student_code, student_name, shared_test_script, language
        )

    def _evaluate_standalone(
        self,
        student_code: str,
        student_name: str,
        shared_test_script: Optional[str],
        language: str = "java",
    ) -> dict:
        from core.tools.java_executor import run_java_test_script
        from core.tools.cpp_executor import run_cpp_test_script

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
                raise ValueError(
                    f"Unsupported language for dynamic execution: {language}"
                )

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

        system_msg_template = self.prompt_manager.read_prompt(
            "legacy/fallback_instructions.txt"
        )
        system_msg = system_msg_template.replace(
            "__SCHEMA__", json.dumps(self.grading_schema)
        ).replace("__TASK__", self.task_description)

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

            try:
                res = json.loads(clean_content)
            except json.JSONDecodeError:
                try:
                    res = ast.literal_eval(clean_content)
                except Exception:
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
