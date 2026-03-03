from pydantic import BaseModel, Field
from typing import List, Optional

class Requirements(BaseModel):
    problem: str
    inputs: List[str]
    outputs: List[str]
    constraints: List[str]
    edge_cases: List[str]
    acceptance_criteria: List[str]
    non_functional_requirements: List[str] = Field(default_factory=list)

class CodePack(BaseModel):
    filename: str
    code: str

class ReviewResult(BaseModel):
    approved: bool
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class TestPack(BaseModel):
    module_filename: str
    module_import: str
    entrypoint: str
    filename: str
    code: str


class DocumentationPack(BaseModel):
    filename: str
    content: str


class DeploymentPack(BaseModel):
    filename: str
    content: str

class PytestResult(BaseModel):
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    
class RunResult(BaseModel):
    run_id: str
    user_request: str
    final_approved: bool
    requirements: Requirements
    code: CodePack
    tests: TestPack | None = None
    documentation: DocumentationPack | None = None
    deployment: DeploymentPack | None = None
    test_result: PytestResult | None = None
    review: ReviewResult
    llm_review: ReviewResult | None = None
    iterations: int
    note: Optional[str] = None
