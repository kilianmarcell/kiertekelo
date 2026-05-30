from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent

OPENROUTER_API_KEY = ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = "openai/gpt-4o"
MODEL_MINI = "openai/gpt-4o-mini"

LLM_TEMPERATURE = 0.1
LLM_TOP_P = 0.1
LLM_MAX_TOKENS = 1000

STUDENT_EVALUATION_TIMEOUT_SECONDS = 20

CPP_COMPILER_PATH = ""  # r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\g++.exe"
