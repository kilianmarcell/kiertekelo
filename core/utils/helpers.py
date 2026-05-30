import os
import re
from pathlib import Path


def load_task_description(root_dir: Path) -> str:
    task_file = root_dir / "datas" / "task.txt"
    if not task_file.exists():
        raise RuntimeError(f"Task file not found: {task_file}")
    with open(task_file, encoding="utf-8-sig") as f:
        return f.read().strip()


def extract_class_name_from_task(task_description: str) -> str:
    match0 = re.search(r"(\w+):\s*\{\{class\}\}", task_description, re.IGNORECASE)
    if match0:
        return match0.group(1)

    match_hu = re.search(r"(\w+)\s+néven", task_description, re.IGNORECASE)
    if match_hu and match_hu.group(1).lower() not in [
        "osztály",
        "osztályt",
        "néven",
        "a",
        "az",
    ]:
        return match_hu.group(1)

    match1 = re.search(r"(\w+)\s+class", task_description, re.IGNORECASE)
    match2 = re.search(r"class\s+(\w+)", task_description, re.IGNORECASE)
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


def detect_language(content: str = "", filename: str = "") -> str:
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
