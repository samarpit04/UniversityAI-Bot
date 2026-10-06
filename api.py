import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Header, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from core.config import settings
from core.schema import (
    AskRequest, AskResponse, IngestResponse, HealthResponse,
    Citation, ToolInvocation, AppliedRule, SourceRegisterItem
)
from core.database import (
    get_connection, get_source_register, insert_source_document,
    get_audit_record, get_all_students, get_student
)
from core.vector_store import get_collection, index_document, initialize_vector_store
from core.workflow import run_workflow

app = FastAPI(
    title="NSUT AI-Powered University Student Services Assistant",
    description="FastAPI Backend meeting HCLTech Hackathon Section 6 Mandatory Contract",
    version="1.0.0"
)

# Enable CORS for Streamlit or web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Ensure vector store is initialized
    initialize_vector_store()

@app.post("/ask", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    x_student_id: Optional[str] = Header(None, alias="X-Student-Id")
):
    """
    POST /ask endpoint:
    - Header X-Student-Id identifies the logged-in student (optional for general questions).
    - Body: question, optional as_of_date (YYYY-MM-DD, defaults to today).
    """
    as_of_date = req.as_of_date or datetime.now().strftime("%Y-%m-%d")
    
    result = run_workflow(
        question=req.question,
        student_id=x_student_id,
        as_of_date=as_of_date
    )
    
    citations = [
        Citation(
            doc_id=c["doc_id"],
            title=c["title"],
            section=c.get("section", "General"),
            page=str(c.get("page", "1")),
            version=str(c.get("version", "1.0")),
            effective_from=str(c.get("effective_from", ""))
        ) for c in result.get("citations", [])
    ]
    
    tools_invoked = [
        ToolInvocation(
            tool=t["tool"],
            input=t["input"],
            output=t["output"]
        ) for t in result.get("tools_invoked", [])
    ]
    
    applied_rules = [
        AppliedRule(
            rule_id=r["rule_id"],
            value=str(r["value"]),
            source_doc_id=r["source_doc_id"]
        ) for r in result.get("applied_rules", [])
    ]
    
    return AskResponse(
        trace_id=result["trace_id"],
        answer=result["answer"],
        answer_type=result["answer_type"],
        citations=citations,
        tools_invoked=tools_invoked,
        applied_rules=applied_rules,
        conflicts_detected=result.get("conflicts_detected", []),
        explanation=result.get("explanation", ""),
        as_of_date=as_of_date
    )

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON string with Annex B metadata fields")
):
    """
    POST /ingest endpoint:
    Add a document while running. Multipart: the file plus a metadata JSON with Source Register fields (Annex B).
    Returns doc_id, chunks_indexed, status.
    """
    try:
        meta_dict = json.loads(metadata)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON metadata: {str(e)}")
        
    doc_id = meta_dict.get("doc_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Metadata must include 'doc_id'")
        
    file_bytes = await file.read()
    content_text = file_bytes.decode("utf-8", errors="replace")
    
    # Store in SQLite Source Register
    meta_dict["content"] = content_text
    insert_source_document(meta_dict)
    
    # Index in ChromaDB live
    title = meta_dict.get("title", doc_id)
    chunks_count = index_document(
        doc_id=doc_id,
        title=title,
        content=content_text,
        metadata=meta_dict
    )
    
    return IngestResponse(
        doc_id=doc_id,
        chunks_indexed=chunks_count,
        status="indexed"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    GET /health endpoint: Readiness status of API, vector store, SQLite, and LLM.
    """
    # SQLite check
    students = get_all_students()
    docs = get_source_register()
    sqlite_status = "ready" if len(students) > 0 else "empty"
    
    # Vector store check
    col = get_collection()
    v_status = f"ready ({col.count()} chunks)" if col else "error"
    
    if settings.HUGGINGFACE_ACCESS_TOKEN:
        llm_status = f"HuggingFace ({settings.HF_MODEL})"
    elif not settings.MOCK_LLM:
        llm_status = f"ollama ({settings.OLLAMA_MODEL})"
    else:
        llm_status = "mock/grounded_deterministic (Ollama fallback)"
    
    return HealthResponse(
        status="healthy",
        api="online",
        vector_store=v_status,
        sqlite=sqlite_status,
        llm=llm_status,
        student_count=len(students),
        docs_count=len(docs)
    )

@app.get("/audit/{trace_id}")
async def get_audit(trace_id: str):
    """
    GET /audit/{trace_id} endpoint: Full audit record for one response per Annex D.
    """
    record = get_audit_record(trace_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Audit record for trace_id '{trace_id}' not found.")
    return record

@app.get("/sources")
async def get_sources():
    """
    GET /sources endpoint: Source Register listing all ingested documents and their metadata.
    """
    return get_source_register()

@app.post("/admin/load-students")
async def load_students(file: UploadFile = File(...)):
    """
    Admin loader for judges test data in Annex C schema.
    """
    content = (await file.read()).decode("utf-8")
    lines = content.strip().split("\n")
    import csv
    reader = csv.DictReader(lines)
    count = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        for row in reader:
            if "student_id" in row and "full_name" in row:
                cursor.execute("""
                    INSERT OR REPLACE INTO students (
                        student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["student_id"], row["full_name"], row.get("programme", "B.Tech CSE"),
                    int(row.get("batch_year", 2023)), int(row.get("current_semester", 5)),
                    float(row.get("cgpa", 7.5)), int(row.get("active_backlogs", 0))
                ))
                count += 1
        conn.commit()
    return {"status": "success", "students_loaded": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
