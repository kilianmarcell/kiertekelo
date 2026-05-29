import subprocess
import os
import tempfile
import time
from langchain.tools import tool

@tool
def run_python_test_script(script_content: str, timeout: int = 5) -> str:
    """Executes a Python test script and returns the stdout and stderr."""
    with tempfile.NamedTemporaryFile(
        suffix=".py", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp_name = tmp.name
        tmp.write(script_content)
    try:
        start_time = time.perf_counter()
        result = subprocess.run(
            ["python", tmp_name],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        duration = round(time.perf_counter() - start_time, 3)
        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        if not output:
            output.append("Script executed successfully with no output.")
        status = (
            "SUCCESS"
            if result.returncode == 0
            else f"FAILED (exit code {result.returncode})"
        )
        return f"Status: {status}\nDuration: {duration}s\n\n" + "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error during execution: {str(e)}"
    finally:
        try:
            os.remove(tmp_name)
        except:
            pass
