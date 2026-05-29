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


class EvaluatorUtilsMixin:
    def reset_counters(self):
        self.total_tokens = 0
        self.total_cost = 0

    def _load_task_description(self) -> str:
        task_file = os.path.join(_ROOT_DIR, "datas", "task.txt")
        if not os.path.exists(task_file):
            raise RuntimeError(f"Task file not found: {task_file}")
        with open(task_file, encoding="utf-8-sig") as f:
            return f.read().strip()

    def _read_prompt_file(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        raise FileNotFoundError(f"Prompt file not found: {path}")

    def _build_system_msg(self) -> str:
        try:
            parts = []
            parts.append(
                self._read_prompt_file(os.path.join(_COMMON_PROMPTS_DIR, "role.txt"))
            )

            if os.path.exists(_SCHEMA_PARTS_DIR):
                part_files = sorted(
                    [f for f in os.listdir(_SCHEMA_PARTS_DIR) if f.endswith(".txt")]
                )
                for name in part_files:
                    parts.append(
                        self._read_prompt_file(os.path.join(_SCHEMA_PARTS_DIR, name))
                    )

            return "\n\n".join(parts) if parts else ""
        except Exception as e:
            raise RuntimeError(f"Error building system message: {e}")

    def _extract_class_name_from_task(
        self,
    ) -> str:
        match0 = re.search(
            r"(\w+):\s*\{\{class\}\}", self.task_description, re.IGNORECASE
        )
        if match0:
            return match0.group(1)

        match_hu = re.search(r"(\w+)\s+néven", self.task_description, re.IGNORECASE)
        if match_hu and match_hu.group(1).lower() not in [
            "osztály",
            "osztályt",
            "néven",
            "a",
            "az",
        ]:
            return match_hu.group(1)

        match1 = re.search(r"(\w+)\s+class", self.task_description, re.IGNORECASE)
        match2 = re.search(r"class\s+(\w+)", self.task_description, re.IGNORECASE)
        name = "Deck"
        if match1 and match1.group(1).lower() not in [
            "generic",
            "java",
            "python",
            "a",
            "the",
        ]:
            name = match1.group(1)
        elif match2 and match2.group(1).lower() not in [
            "generic",
            "java",
            "python",
            "a",
            "the",
            "in",
            "is",
        ]:
            name = match2.group(1)
        return name

    def detect_language(self, content: str = "", filename: str = "") -> str:
        content_lower = content.lower()
        if (
            "java" in filename.lower()
            or "public class" in content_lower
            or "List<" in content
        ):
            return "java"
        if (
            "#include" in content_lower
            or "template<" in content_lower
            or "namespace" in content_lower
            or "std::" in content_lower
        ):
            return "cpp"
        return "cpp"
