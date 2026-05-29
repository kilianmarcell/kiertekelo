# LLM-Based Code Evaluator

A Python project that evaluates student code submissions from JPorta-style JSON exports using Large Language Models (LLMs). It supports multiple programming languages (Java, C++, Python) and offers three distinct evaluation strategies (Original, Testcases, Mental Execution).

## Features

- **Multiple Evaluation Modes**:
  - `Original`: Holistic, single-pass evaluation based on intent and logic.
  - `Testcases`: Dynamic schema and executable test generation. The system generates tests, compiles them with the student's code (using local executors), and falls back to smart static analysis if execution fails.
  - `Mental Execution`: The LLM generates edge cases and mentally traces the variables step-by-step.
- **Robust JSON Parsing**: Features a multi-layered auto-repair mechanism for fixing malformed LLM outputs.
- **Modular Architecture**: Clean separation between CLI (`main.py`), orchestration (`core/evaluation_runner.py`), and core business logic (`core/mixins`).
- **Detailed Reporting**: Generates aggregated JSON summaries and individual detailed text reports per student.

## Project Structure

```text
kiertekelo/
├── settings.example.py      # Configuration template (rename to settings.py)
├── main.py                  # CLI entry point
├── core/                    # Core business logic
│   ├── langchain_evaluator.py # Main evaluator class
│   ├── evaluation_runner.py   # Orchestrator loop
│   ├── mixins/                # Evaluation strategies and schemas
│   ├── schemas/               # Pydantic response models
│   ├── tools/                 # Dynamic code executors (Java, C++, Python) & JSON repair
│   └── utils/                 # Data loaders and report builders
├── datas/                   # Input JPorta JSON files
├── prompts/                 # Modular LLM instructions (legacy, mental, schema_parts, etc.)
└── output/                  # Generated results (scores/ directory and evaluation_results.json)
```

## Setup

### 1. Requirements

Python 3.9 or newer is required.

```bash
pip install -r requirements.txt
```

### 2. Configuration

1. Copy or rename `settings.example.py` to `settings.py`.
2. Open `settings.py` and configure your API keys and models:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key.
   - Set the `CPP_COMPILER_PATH` if you are on Windows and using the C++ executor.
   - Adjust LLM parameters (Temperature, Top-P, Tokens) as needed.

*Note: `settings.py` is ignored by Git to keep your API keys secure.*

## Usage

1. Place your JPorta export JSON file in the `datas/` folder.
2. Run the application:

```bash
python main.py
```

3. Follow the CLI prompts to select your input file and choose the evaluation mode (Simple AI or Universal Testcase-based).

### Output Files

After a successful run, results are saved in the `output/` directory:
- `evaluation_results.json`: An aggregated JSON containing all student scores, durations, and overall run statistics.
- `output/scores/<StudentName>.txt`: Detailed, human-readable text files containing the score, percentage, and professional LLM explanation for each student.

## Common Errors

- `ModuleNotFoundError`: Ensure you have activated your virtual environment and installed dependencies.
- `LLM hiba / Rate Limit`: Verify your API key and check OpenRouter credits/status.
- `JSON parse hiba`: Handled internally in most cases, but extreme hallucinations might still fail. Check the model temperature.
