import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.config import settings

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    Path(settings.SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Students Table (Annex C)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                programme TEXT NOT NULL,
                batch_year INTEGER NOT NULL,
                current_semester INTEGER NOT NULL,
                cgpa REAL NOT NULL,
                active_backlogs INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # 2. Courses Table (Annex C)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_code TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                programme TEXT NOT NULL,
                semester INTEGER NOT NULL,
                credits INTEGER NOT NULL
            )
        """)
        
        # 3. Attendance Table (Annex C)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                student_id TEXT NOT NULL,
                course_code TEXT NOT NULL,
                classes_held INTEGER NOT NULL,
                classes_attended INTEGER NOT NULL,
                PRIMARY KEY (student_id, course_code),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_code) REFERENCES courses(course_code)
            )
        """)
        
        # 4. Results Table (Annex C)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_code TEXT NOT NULL,
                exam_session TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                internal_marks INTEGER NOT NULL,
                external_marks INTEGER NOT NULL,
                total_marks INTEGER NOT NULL,
                max_marks INTEGER NOT NULL DEFAULT 100,
                result TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_code) REFERENCES courses(course_code)
            )
        """)
        
        # 5. Rule Registry Table (Annex C)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_registry (
                rule_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                parameter TEXT NOT NULL,
                operator TEXT NOT NULL,
                value TEXT NOT NULL,
                scope_programmes TEXT NOT NULL DEFAULT 'ALL',
                scope_batches TEXT NOT NULL DEFAULT 'ALL',
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                source_doc_id TEXT NOT NULL,
                source_section TEXT NOT NULL
            )
        """)
        
        # 6. Source Register Table (Annex B)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_register (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                issuer TEXT NOT NULL,
                authority_level INTEGER NOT NULL,
                doc_type TEXT NOT NULL,
                version TEXT NOT NULL,
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                supersedes TEXT,
                scope_programmes TEXT NOT NULL DEFAULT 'ALL',
                scope_batches TEXT NOT NULL DEFAULT 'ALL',
                provenance TEXT NOT NULL DEFAULT '',
                retrieved_on TEXT NOT NULL DEFAULT '',
                synthetic TEXT NOT NULL DEFAULT 'N',
                content TEXT DEFAULT ''
            )
        """)
        
        # 7. Audit Records Table (Annex D)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_records (
                trace_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                student_id TEXT,
                question TEXT NOT NULL,
                question_category TEXT NOT NULL,
                sources_retrieved TEXT NOT NULL,
                precedence_decision TEXT,
                tools_invoked TEXT NOT NULL,
                applied_rules TEXT NOT NULL,
                answer_type TEXT NOT NULL,
                answer TEXT NOT NULL,
                model TEXT NOT NULL,
                llm_calls INTEGER NOT NULL,
                tokens INTEGER NOT NULL,
                latency_ms REAL NOT NULL
            )
        """)
        conn.commit()

# --- Helper Queries ---

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_students() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY student_id")
        return [dict(r) for r in cursor.fetchall()]

def get_student_attendance(student_id: str, course_code: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if course_code:
            cursor.execute("""
                SELECT a.*, c.course_name 
                FROM attendance a
                JOIN courses c ON a.course_code = c.course_code
                WHERE a.student_id = ? AND a.course_code = ?
            """, (student_id, course_code))
        else:
            cursor.execute("""
                SELECT a.*, c.course_name 
                FROM attendance a
                JOIN courses c ON a.course_code = c.course_code
                WHERE a.student_id = ?
            """, (student_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_student_results(student_id: str, course_code: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if course_code:
            cursor.execute("""
                SELECT r.*, c.course_name
                FROM results r
                JOIN courses c ON r.course_code = c.course_code
                WHERE r.student_id = ? AND r.course_code = ?
                ORDER BY r.exam_session DESC
            """, (student_id, course_code))
        else:
            cursor.execute("""
                SELECT r.*, c.course_name
                FROM results r
                JOIN courses c ON r.course_code = c.course_code
                WHERE r.student_id = ?
                ORDER BY r.exam_session DESC
            """, (student_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_rules_by_parameter(parameter: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rule_registry WHERE parameter = ?", (parameter,))
        return [dict(r) for r in cursor.fetchall()]

def get_all_rules() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rule_registry ORDER BY rule_id")
        return [dict(r) for r in cursor.fetchall()]

def insert_source_document(doc: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO source_register (
                doc_id, title, issuer, authority_level, doc_type, version,
                effective_from, effective_to, supersedes, scope_programmes,
                scope_batches, provenance, retrieved_on, synthetic, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc["doc_id"], doc["title"], doc["issuer"], int(doc["authority_level"]),
            doc["doc_type"], doc["version"], doc["effective_from"], doc.get("effective_to", ""),
            doc.get("supersedes", ""), doc.get("scope_programmes", "ALL"), doc.get("scope_batches", "ALL"),
            doc.get("provenance", ""), doc.get("retrieved_on", ""), doc.get("synthetic", "N"),
            doc.get("content", "")
        ))
        conn.commit()

def get_source_register() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM source_register ORDER BY authority_level ASC, effective_from DESC")
        return [dict(r) for r in cursor.fetchall()]

def save_audit_record(record: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO audit_records (
                trace_id, timestamp, student_id, question, question_category,
                sources_retrieved, precedence_decision, tools_invoked, applied_rules,
                answer_type, answer, model, llm_calls, tokens, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["trace_id"],
            record["timestamp"],
            record.get("student_id"),
            record["question"],
            record["question_category"],
            json.dumps(record.get("sources_retrieved", [])),
            record.get("precedence_decision"),
            json.dumps(record.get("tools_invoked", [])),
            json.dumps(record.get("applied_rules", [])),
            record["answer_type"],
            record["answer"],
            record.get("model", "llama3.1:8b"),
            record.get("llm_calls", 1),
            record.get("tokens", 0),
            record.get("latency_ms", 0.0)
        ))
        conn.commit()

def get_audit_record(trace_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_records WHERE trace_id = ?", (trace_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["sources_retrieved"] = json.loads(res["sources_retrieved"] or "[]")
        res["tools_invoked"] = json.loads(res["tools_invoked"] or "[]")
        res["applied_rules"] = json.loads(res["applied_rules"] or "[]")
        return res
