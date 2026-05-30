from pathlib import Path

from core.langchain_evaluator import LangChainCodeEvaluator
from core.utils.data_loader import load_students_from_json
from core.evaluation_runner import run_evaluations

_ROOT_DIR = Path(__file__).parent


def main():
    print("Automated Java/C++ Code Evaluator")

    json_filename = input("Input JSON filename: ").strip()
    json_path = _ROOT_DIR / "datas" / json_filename

    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return

    print("\nEvaluation Mode:")
    print("  1 - Simple AI evaluation (original)")
    print("  2 - Universal Testcase-based evaluation (testcases)")
    print("  3 - Mental Execution evaluation (mental)")
    mode_choice = input("Choice (1/2/3): ")
    if mode_choice == "1":
        eval_mode = "original"
    elif mode_choice == "3":
        eval_mode = "mental"
    else:
        eval_mode = "testcases"

    evaluator = LangChainCodeEvaluator()
    students_data = load_students_from_json(str(json_path))

    run_evaluations(
        evaluator=evaluator,
        students_data=students_data,
        eval_mode=eval_mode,
        json_filename=json_filename,
        root_dir=_ROOT_DIR,
    )


if __name__ == "__main__":
    main()
