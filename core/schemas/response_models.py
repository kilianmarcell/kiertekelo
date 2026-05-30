from pydantic import BaseModel, Field
from typing import List


class TestCaseSchema(BaseModel):
    name: str = Field(description="The short name of the test case.")
    weight: int = Field(
        description="The weight of the test case (the total sum of weights should be 100)."
    )
    logic: str = Field(
        description="The Java, C++, or Python code of the test case (body only)."
    )


class TestScriptSchema(BaseModel):
    test_cases: List[TestCaseSchema] = Field(
        description="The list of test cases generated for the task."
    )


class HolisticEvaluationResult(BaseModel):
    score: int = Field(
        description="The percentage score for the student's code (0-100)."
    )
    evaluation: str = Field(
        description="A detailed, pedagogical text evaluation of the code."
    )


class MentalTestResult(BaseModel):
    test_case: str = Field(description="The name or description of the test case.")
    expected: str = Field(description="The expected outcome.")
    trace: str = Field(
        description="Step-by-step mental trace of the student's code running the test case."
    )
    passed: bool = Field(description="Whether the code passed this test case.")


class MentalEvaluationResult(BaseModel):
    test_results: List[MentalTestResult] = Field(
        description="List of results for each mental test case."
    )
    score_calculation_reasoning: str = Field(
        description="Step-by-step reasoning counting the passed tests out of total tests to calculate the final percentage. Count out loud."
    )
    final_percentage: int = Field(
        description="The final percentage score from 0 to 100 based strictly on the ratio of passed tests."
    )
    overall_evaluation: str = Field(
        description="A brief summary of the mental execution results."
    )
