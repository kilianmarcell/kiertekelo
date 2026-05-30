import json
from typing import Dict


def load_students_from_json(json_path: str) -> Dict:
    with open(json_path, encoding="utf-8-sig") as f:
        return json.load(f)


def extract_student_code(data: Dict) -> str:
    if "code" in data:
        return data["code"]
    if "codes" in data:
        try:
            for c in reversed(data["codes"]):
                if c.strip().startswith("Submit:"):
                    return c.replace("Submit:", "").strip()
            return data["codes"][-1]
        except (IndexError, TypeError):
            return ""
    return ""
