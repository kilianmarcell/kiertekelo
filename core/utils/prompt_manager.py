import os
from pathlib import Path


class PromptManager:

    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.prompts_dir = self.root_dir / "prompts"
        self.schema_parts_dir = self.prompts_dir / "schema_parts"
        self.test_gen_parts_dir = self.prompts_dir / "test_gen_parts"
        self.tester_templates_dir = self.prompts_dir / "tester_templates"
        self.common_prompts_dir = self.prompts_dir / "common"
        self.legacy_prompts_dir = self.prompts_dir / "legacy"
        self.mental_prompts_dir = self.prompts_dir / "mental"

    def read_prompt(self, relative_path: str) -> str:
        path = self.prompts_dir / relative_path
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        raise FileNotFoundError(f"Prompt file not found: {path}")

    def build_system_msg_from_schema_parts(self) -> str:
        try:
            parts = []
            parts.append(self.read_prompt("common/role.txt"))

            if self.schema_parts_dir.exists():
                part_files = sorted(
                    [
                        f.name
                        for f in self.schema_parts_dir.iterdir()
                        if f.name.endswith(".txt")
                    ]
                )
                for name in part_files:
                    parts.append(self.read_prompt(f"schema_parts/{name}"))

            return "\n\n".join(parts) if parts else ""
        except Exception as e:
            raise RuntimeError(f"Error building system message: {e}")
