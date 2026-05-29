import json
import os
import time
from pathlib import Path
from typing import Dict, Any

from core.langchain_evaluator import LangChainCodeEvaluator
from core.utils.score_output_builder import build_score_report_lines
from core.utils.data_loader import extract_student_code


def run_evaluations(
    evaluator: LangChainCodeEvaluator,
    students_data: Dict[str, Any],
    eval_mode: str,
    json_filename: str,
    root_dir: Path,
) -> Dict[str, Any]:

    first_student_id = next(iter(students_data))
    first_code = extract_student_code(students_data[first_student_id])
    detected_lang = evaluator.detect_language(content=first_code)

    print(f"\nSource file: {json_filename}")
    print(f"Number of students loaded: {len(students_data)}")
    print(f"Detected language: {detected_lang}")

    shared_test_script = None
    if eval_mode == "testcases":
        print("Generating universal grading schema...")
        evaluator.generate_grading_schema()

        print(f"Generating {detected_lang} test script...")
        for attempt in range(2):
            try:
                shared_test_script = evaluator.generate_shared_test_script(
                    language=detected_lang
                )
                if "TOTAL_SCORE:" in shared_test_script:
                    print("ok")
                    tester_ext = {"java": "java", "cpp": "cpp"}.get(
                        detected_lang, "txt"
                    )
                    tester_save_path = (
                        root_dir / "output" / f"SharedTester.{tester_ext}"
                    )
                    os.makedirs(root_dir / "output", exist_ok=True)
                    with open(tester_save_path, "w", encoding="utf-8") as f:
                        f.write(shared_test_script)
                    break
                else:
                    if attempt == 0:
                        print("\nMissing TOTAL_SCORE. Retrying...")
                    else:
                        print(
                            "\nFailed to generate valid test script. Falling back to Static Only."
                        )
                        shared_test_script = None
            except Exception as e:
                print(f"\nError: {e}")

        if not shared_test_script:
            print("Proceeding with Static Fallback only.")

    results = []
    output_dir = root_dir / "output" / "scores"
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    for student_id, data in students_data.items():
        student_code = extract_student_code(data)
        student_name = student_id
        manual_point = data.get("results", {}).get("man", {}).get("point")

        try:
            start_eval = time.time()
            if eval_mode == "testcases":
                res = evaluator.evaluate_standalone(
                    student_code,
                    student_name,
                    shared_test_script,
                    language=detected_lang,
                )
            else:
                res = evaluator.evaluate(
                    student_code, student_name, evaluation_mode=eval_mode
                )

            duration = time.time() - start_eval

            report_lines = build_score_report_lines(
                student_name=student_name,
                score=res.get("score", 0),
                percentage=res.get("percentage"),
                evaluation_text=res.get("evaluation", ""),
                manual_aligned_score=manual_point,
            )

            report_file = output_dir / f"{student_id}.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))

            res["id"] = student_id
            res["duration_seconds"] = round(duration, 3)
            results.append(res)
            print(f"Success: {student_id} ({duration:.2f}s)")

        except Exception as e:
            print(f"Failed: {student_id} - {e}")
            results.append({"id": student_id, "success": False, "error": str(e)})

    total_duration = time.time() - start_time
    summary = {
        "run": {
            "mode": eval_mode,
            "language": detected_lang,
            "total_duration_seconds": round(total_duration, 3),
            "evaluated_count": len(results),
            "failed_count": sum(1 for r in results if not r.get("success", True)),
        },
        "evaluations": results,
    }

    results_json_path = root_dir / "output" / "evaluation_results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: output/evaluation_results.json")
    print(f"Total runtime: {total_duration:.3f}s")
    print(f"Total Tokens: {evaluator.total_tokens}")
    print(f"Total Cost: ${evaluator.total_cost:.4f}")

    return summary
