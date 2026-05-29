def get_fallback_grading_schema(c: str) -> dict:
    return {
        "task_name": f"{c} Implementation",
        "categories": [
            {
                "id": 1,
                "name": "Class & Structure",
                "weight": 10,
                "patterns": [rf"class\s+{c}"],
            },
            {
                "id": 2,
                "name": "Member Variables",
                "weight": 20,
                "patterns": [r"private", r";"],
            },
            {
                "id": 3,
                "name": "Constructors",
                "weight": 20,
                "patterns": [rf"{c}\s*\("],
            },
            {
                "id": 4,
                "name": "Methods & Logic",
                "weight": 40,
                "patterns": [r"public", r"\(", r"\{"],
            },
            {
                "id": 5,
                "name": "Syntax & Quality",
                "weight": 10,
                "patterns": [r"\}"],
            },
        ],
    }
