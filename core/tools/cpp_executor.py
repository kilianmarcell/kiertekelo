import subprocess
import os
import tempfile
import time
import re
from langchain.tools import tool
from settings import CPP_COMPILER_PATH


def _find_cpp_compiler() -> str:
    if os.path.exists(CPP_COMPILER_PATH):
        return CPP_COMPILER_PATH
    return "g++"


@tool
def run_cpp_test_script(
    script_content: str, student_code: str = "", timeout: int = 15
) -> str:
    """Compiles and runs C++ code (student + test script) and returns the output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cpp_path = os.path.join(tmp_dir, "test.cpp")
        exe_path = os.path.join(tmp_dir, "test.exe")

        cleaned = student_code
        cleaned = re.sub(
            r"(\w+)\s*\(\s*(\w+)\s*&\s*(\w+)\s*\)", r"\1(const \2& \3)", cleaned
        )

        cleaned = re.sub(r"(size|capacity)\s*\(\s*\)\s*\{", r"\1() const {", cleaned)
        cleaned = re.sub(r"\bsiz_t\b", "size_t", cleaned)
        cleaned = re.sub(r"\bstatics\b", "static", cleaned)

        full_code = cleaned + "\n\n" + script_content
        if "#include" not in full_code:
            full_code = (
                "#include <iostream>\n#include <vector>\n#include <string>\n#include <stdexcept>\n"
                + full_code
            )

        with open(cpp_path, "w", encoding="utf-8") as f:
            f.write(full_code)

        try:
            compiler = _find_cpp_compiler()
            start_perf = time.perf_counter()

            comp = subprocess.run(
                [compiler, "-O2", "-static", "test.cpp", "-o", exe_path],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
            )

            if comp.returncode != 0:
                return f"COMPILATION_FAILED\n\nOutput:\n{comp.stderr}"

            run_proc = subprocess.run(
                [exe_path], cwd=tmp_dir, capture_output=True, text=True, timeout=timeout
            )

            duration = round(time.perf_counter() - start_perf, 3)
            status = (
                "SUCCESS"
                if run_proc.returncode == 0
                else f"FAILED (exit code {run_proc.returncode})"
            )
            output = run_proc.stdout + (
                f"\nSTDERR:\n{run_proc.stderr}" if run_proc.stderr else ""
            )
            return f"Status: {status}\nDuration: {duration}s\n\nOutput:\n{output}"

        except subprocess.TimeoutExpired:
            return f"Execution timed out after {timeout} seconds."
        except Exception as e:
            return f"Error during execution: {str(e)}"
