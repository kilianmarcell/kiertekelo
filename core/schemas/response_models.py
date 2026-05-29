from pydantic import BaseModel, Field
from typing import List


class TestCaseSchema(BaseModel):
    name: str = Field(description="A teszteset rövid neve.")
    weight: int = Field(description="A teszteset súlya (összesen 100 pont legyen).")
    logic: str = Field(description="A teszteset Java vagy C++ kódja (csak a törzs).")


class TestScriptSchema(BaseModel):
    test_cases: List[TestCaseSchema] = Field(
        description="A feladathoz generált tesztesetek listája."
    )
