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
from .response_models import TestScriptSchema
from .fallback_schema import get_fallback_grading_schema

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROMPTS_DIR = os.path.join(_ROOT_DIR, "prompts")
_SCHEMA_PARTS_DIR = os.path.join(_PROMPTS_DIR, "schema_parts")
_TEST_GEN_PARTS_DIR = os.path.join(_PROMPTS_DIR, "test_gen_parts")
_TESTER_TEMPLATES_DIR = os.path.join(_PROMPTS_DIR, "tester_templates")
_COMMON_PROMPTS_DIR = os.path.join(_PROMPTS_DIR, "common")


class SchemaGeneratorMixin:
    def generate_grading_schema(self) -> Dict:
        c = self._extract_class_name_from_task()
        system_msg = self._build_system_msg()

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
            self.grading_schema = get_fallback_grading_schema(c)
        return self.grading_schema

    def generate_shared_test_script(self, language: str = "java") -> str:
        class_name = self._extract_class_name_from_task()
        parser = PydanticOutputParser(pydantic_object=TestScriptSchema)

        try:
            system_msg = "\n\n".join(
                self._read_prompt_file(os.path.join(_TEST_GEN_PARTS_DIR, f))
                for f in [
                    "../common/role.txt",
                    "01_goal.txt",
                    f"02_{language}.txt",
                    "03_footer.txt",
                ]
            )
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
        template_path = os.path.join(_TESTER_TEMPLATES_DIR, f"{language}_template.txt")
        template = self._read_prompt_file(template_path)

        if template:
            return template.replace("__CLASS_NAME__", class_name).replace(
                "__BODY__", body_str
            )

        return ""
