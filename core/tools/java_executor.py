import subprocess
import os
import tempfile
import time
import re
import shutil
from langchain.tools import tool

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SOMELIST_PATH = os.path.join(_ROOT_DIR, "prompts", "tester_templates", "SomeList.java")


@tool
def run_java_test_script(
    script_content: str, student_code: str = "", timeout: int = 15
) -> str:
    """Compiles and runs Java student code against a provided Tester.java script."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        if "SomeList" in script_content or "SomeList" in student_code:
            somelist_path = os.path.join(tmp_dir, "SomeList.java")
            shutil.copy(_SOMELIST_PATH, somelist_path)

        student_filename = "Student.java"
        if student_code:
            if "import java.util" not in student_code:
                student_code = (
                    "import java.util.*;\nimport java.util.Collections;\n"
                    + student_code
                )

            class_match = re.search(r"(?:public\s+)?class\s+(\w+)", student_code)
            if class_match:
                student_filename = class_match.group(1) + ".java"

            student_path = os.path.join(tmp_dir, student_filename)

            cleaned = re.sub(r"public\s+class", "class", student_code)
            cleaned = re.sub(r"\bprivte\b", "private", cleaned)
            cleaned = re.sub(r"\bretrun\b", "return", cleaned)
            cleaned = re.sub(r"\blenght\b", "length", cleaned)
            cleaned = re.sub(r"(\breturn\s+[^;{}]+?)(?=\s*[\r\n\}]|$)", r"\1;", cleaned)

            if re.search(r"<\s*T\s*>|\bT\s+\w+\s*\(", cleaned) and not re.search(
                r"class\s+\w+\s*<\s*T\s*>", cleaned
            ):
                cleaned = re.sub(
                    r"(class\s+\w+)(\s*\{|\s+extends|\s+implements)",
                    r"\1<T>\2",
                    cleaned,
                )

            cleaned = re.sub(
                r"(class\s+(\w+).*?public\s+)\2<[^>]*>\s*\(",
                r"\1 \2(",
                cleaned,
                flags=re.DOTALL,
            )

            cleaned = re.sub(r"\(([\w\s,<>]+?),\s*(\w+)\s*\)", r"(\1 \2)", cleaned)
            cleaned = re.sub(
                r"new\s+(ArrayList|SomeList|LinkedList|HashSet|HashMap)\s*([^(\w])",
                r"new \1()\2",
                cleaned,
            )

            with open(student_path, "w", encoding="utf-8") as f:
                f.write(cleaned)

        tester_path = os.path.join(tmp_dir, "Tester.java")
        with open(tester_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        try:
            start_perf = time.perf_counter()

            for file in os.listdir(tmp_dir):
                if file.endswith(".java") and file not in [
                    student_filename,
                    "Tester.java",
                ]:
                    subprocess.run(
                        ["javac", "-encoding", "utf-8", file],
                        cwd=tmp_dir,
                        capture_output=True,
                    )

            subprocess.run(
                ["javac", "-encoding", "utf-8", "-cp", ".", student_filename],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
            )

            comp_tester = subprocess.run(
                ["javac", "-encoding", "utf-8", "-cp", ".", "Tester.java"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
            )

            if comp_tester.returncode != 0:
                duration = round(time.perf_counter() - start_perf, 3)
                return {
                    "success": False,
                    "status": "TESTER_COMPILATION_FAILED",
                    "duration": duration,
                    "stderr": comp_tester.stderr,
                    "output": f"Error:\n{comp_tester.stderr}",
                }

            run_proc = subprocess.run(
                ["java", "-cp", ".", "Tester"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
            )

            duration = round(time.perf_counter() - start_perf, 3)
            return {
                "success": run_proc.returncode == 0,
                "status": "SUCCESS" if run_proc.returncode == 0 else "EXECUTION_FAILED",
                "duration": duration,
                "stdout": run_proc.stdout,
                "stderr": run_proc.stderr,
                "output": run_proc.stdout
                + (f"\nSTDERR:\n{run_proc.stderr}" if run_proc.stderr else ""),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "TIMEOUT",
                "output": "Execution timed out.",
            }
        except Exception as e:
            return {"success": False, "status": "ERROR", "output": str(e)}
