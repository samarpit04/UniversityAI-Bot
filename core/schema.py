from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field

AnswerType = Literal[
    "retrieved_fact",
    "calculated",
    "not_found",
    "clarification_needed",
    "refused",
    "conflict_flagged"
]

class AskRequest(BaseModel):
    question: str = Field(..., description="The student or user question")
    as_of_date: Optional[str] = Field(None, description="Effective date for document applicability (YYYY-MM-DD)")

class Citation(BaseModel):
    doc_id: str
    title: str
    section: str
    page: str
    version: str
    effective_from: str

class ToolInvocation(BaseModel):
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]

class AppliedRule(BaseModel):
    rule_id: str
    value: str
    source_doc_id: str

class ConflictDetected(BaseModel):
    rule_or_topic: str
    doc1: str
    doc2: str
    reason: str
    resolution: Optional[str] = None

class AskResponse(BaseModel):
    trace_id: str
    answer: str
    answer_type: AnswerType
    citations: List[Citation] = []
    tools_invoked: List[ToolInvocation] = []
    applied_rules: List[AppliedRule] = []
    conflicts_detected: List[Any] = []
    explanation: str = ""
    as_of_date: str

class IngestResponse(BaseModel):
    doc_id: str
    chunks_indexed: int
    status: str

class HealthResponse(BaseModel):
    status: str
    api: str
    vector_store: str
    sqlite: str
    llm: str
    student_count: int
    docs_count: int

class SourceRegisterItem(BaseModel):
    doc_id: str
    title: str
    issuer: str
    authority_level: int  # 1 to 5
    doc_type: str
    version: str
    effective_from: str
    effective_to: Optional[str] = ""
    supersedes: Optional[str] = ""
    scope_programmes: str = "ALL"
    scope_batches: str = "ALL"
    provenance: str = ""
    retrieved_on: str = ""
    synthetic: str = "N"

class AuditRecord(BaseModel):
    trace_id: str
    timestamp: str
    student_id: Optional[str] = None
    question: str
    question_category: str
    sources_retrieved: List[Dict[str, Any]] = []
    precedence_decision: Optional[str] = None
    tools_invoked: List[Dict[str, Any]] = []
    applied_rules: List[Dict[str, Any]] = []
    answer_type: AnswerType
    answer: str
    model: str
    llm_calls: int = 1
    tokens: int = 0
    latency_ms: float = 0.0
