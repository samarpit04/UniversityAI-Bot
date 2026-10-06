import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

from core.config import settings
from core.database import (
    get_all_students, get_student, get_source_register, get_all_rules,
    get_student_attendance, get_audit_record, get_connection
)
from core.workflow import run_workflow

# Configure page
st.set_page_config(
    page_title="NSUT Student Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom minimal styles
st.markdown("""
<style>
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-bottom: 8px;
    }
    .badge-calculated { background-color: #065f46; color: #d1fae5; }
    .badge-retrieved_fact { background-color: #1e40af; color: #dbeafe; }
    .badge-not_found { background-color: #475569; color: #f1f5f9; }
    .badge-refused { background-color: #991b1b; color: #fee2e2; }
    .badge-conflict_flagged { background-color: #9a3412; color: #ffedd5; }
    
    .stChatMessage {
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to query backend or direct fallback
def ask_assistant(question: str, student_id: Optional[str], as_of_date: str) -> Dict[str, Any]:
    # 1. Try FastAPI backend if running
    try:
        headers = {}
        if student_id:
            headers["X-Student-Id"] = student_id
        payload = {"question": question, "as_of_date": as_of_date}
        resp = requests.post(f"{settings.API_BASE_URL}/ask", json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
        
    # 2. Local fallback: invoke LangGraph workflow directly
    res = run_workflow(question=question, student_id=student_id, as_of_date=as_of_date)
    return {
        "trace_id": res["trace_id"],
        "answer": res["answer"],
        "answer_type": res["answer_type"],
        "citations": res.get("citations", []),
        "tools_invoked": res.get("tools_invoked", []),
        "applied_rules": res.get("applied_rules", []),
        "conflicts_detected": res.get("conflicts_detected", []),
        "explanation": res.get("explanation", ""),
        "as_of_date": as_of_date
    }

# ================= SIDEBAR: STUDENT IDENTITY & CONTROLS =================
st.sidebar.title("🎓 Student Portal")

all_students = get_all_students()
student_options = {f"{s['student_id']} - {s['full_name']} ({s['programme']})": s["student_id"] for s in all_students}
student_options["Guest / Unauthenticated Mode"] = None

selected_student_label = st.sidebar.selectbox(
    "Logged In Student",
    list(student_options.keys()),
    index=0,
    help="Identifies the student via request context (X-Student-Id header)"
)
active_student_id = student_options[selected_student_label]

if active_student_id:
    student = get_student(active_student_id)
    if student:
        st.sidebar.markdown(f"""
        **Profile:**
        - **Roll No:** `{student['student_id']}`
        - **Name:** {student['full_name']}
        - **Programme:** {student['programme']}
        - **Semester:** {student['current_semester']} (Batch {student['batch_year']})
        - **CGPA:** `{student['cgpa']}` | **Backlogs:** `{student['active_backlogs']}`
        """)
        
        # Enrolled courses
        att_recs = get_student_attendance(active_student_id)
        if att_recs:
            st.sidebar.markdown("**Enrolled Courses:**")
            for a in att_recs:
                pct = round((a['classes_attended'] / a['classes_held']) * 100, 1)
                st.sidebar.markdown(f"- **{a['course_code']}**: {a['classes_attended']}/{a['classes_held']} ({pct}%)")
else:
    st.sidebar.warning("Guest Mode: Queries for personal records will be refused.")

st.sidebar.divider()
as_of_date_val = st.sidebar.date_input("As-Of Date (Annex A)", datetime(2026, 10, 6))
as_of_date_str = as_of_date_val.strftime("%Y-%m-%d")

if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# ================= MAIN AREA =================
st.title("🏛️ NSUT Student Services Assistant")
st.caption("AI Assistant for Netaji Subhas University of Technology regulations, attendance, and exam eligibility.")

# Main Navigation: Clean 2 tabs
tab_chat, tab_admin = st.tabs(["💬 Student Assistant", "⚙️ Judge & Admin Hub"])

# Initialize session messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TAB 1: STUDENT CHAT ASSISTANT ---
with tab_chat:
    # Quick Prompt Pills
    st.markdown("**Quick Suggestions:**")
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    
    preset_clicked = None
    with col_p1:
        if st.button("📊 My Attendance", use_container_width=True):
            preset_clicked = "what is my attendance"
    with col_p2:
        if st.button("📝 Exam Eligibility", use_container_width=True):
            preset_clicked = "am I eligible for the end-semester exams?"
    with col_p3:
        if st.button("📜 75% Attendance Rule", use_container_width=True):
            preset_clicked = "what is the minimum attendance required to appear for end-semester exams?"
    with col_p4:
        if st.button("📱 Mobile Phone Penalty", use_container_width=True):
            preset_clicked = "what is the punishment for carrying a mobile phone in an exam?"
    with col_p5:
        if st.button("🔮 What-If Placement", use_container_width=True):
            preset_clicked = "if I pass the supplementary exam, will I be eligible for campus placement?"

    # Display past chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                ans_data = msg["content"]
                ans_type = ans_data.get("answer_type", "retrieved_fact")
                badge_class = f"badge-{ans_type}"
                
                st.markdown(f'<span class="badge {badge_class}">{ans_type.upper()}</span>', unsafe_allow_html=True)
                st.markdown(ans_data.get("answer", ""))
                
                # Single neat expander for evidence & tools
                citations = ans_data.get("citations", [])
                tools = ans_data.get("tools_invoked", [])
                rules = ans_data.get("applied_rules", [])
                
                if citations or tools or rules:
                    with st.expander(f"🔍 Evidence, Rules & Tools (Trace: {ans_data.get('trace_id', 'N/A')})", expanded=False):
                        if citations:
                            st.markdown("**📜 Cited Regulations:**")
                            for c in citations:
                                st.markdown(f"- **{c.get('title')}** ({c.get('doc_id')}) — {c.get('section')}, Page {c.get('page')}")
                        if tools:
                            st.markdown("**🧮 Deterministic Calculations (SQLite):**")
                            for t in tools:
                                st.markdown(f"- Tool: `{t.get('tool')}`")
                                st.json(t.get("output", {}))
                        if rules:
                            st.markdown("**📋 Applied Rules:**")
                            for r in rules:
                                st.markdown(f"- Rule `{r.get('rule_id')}`: {r.get('value')} (Source: {r.get('source_doc_id')})")

    # Chat input box
    chat_input_val = st.chat_input("Ask a question about your attendance, exam rules, or eligibility...")
    
    # Process input (either from chat box or preset button)
    user_prompt = preset_clicked if preset_clicked else chat_input_val

    if user_prompt:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("user"):
            st.write(user_prompt)
            
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Processing request..."):
                t0 = time.time()
                resp = ask_assistant(user_prompt, active_student_id, as_of_date_str)
                dur_ms = round((time.time() - t0) * 1000, 1)
                
            ans_type = resp.get("answer_type", "retrieved_fact")
            badge_class = f"badge-{ans_type}"
            
            st.markdown(f'<span class="badge {badge_class}">{ans_type.upper()}</span> <span style="font-size:0.8rem;color:#94a3b8;">({dur_ms}ms)</span>', unsafe_allow_html=True)
            st.markdown(resp.get("answer", ""))
            
            citations = resp.get("citations", [])
            tools = resp.get("tools_invoked", [])
            rules = resp.get("applied_rules", [])
            
            if citations or tools or rules:
                with st.expander(f"🔍 Evidence, Rules & Tools (Trace: {resp.get('trace_id', 'N/A')})", expanded=True):
                    if citations:
                        st.markdown("**📜 Cited Regulations:**")
                        for c in citations:
                            st.markdown(f"- **{c.get('title')}** (`{c.get('doc_id')}`) — {c.get('section')}, Page {c.get('page')}")
                    if tools:
                        st.markdown("**🧮 Deterministic Calculations (SQLite):**")
                        for t in tools:
                            st.markdown(f"- Tool: `{t.get('tool')}`")
                            st.json(t.get("output", {}))
                    if rules:
                        st.markdown("**📋 Applied Rules:**")
                        for r in rules:
                            st.markdown(f"- Rule `{r.get('rule_id')}`: {r.get('value')} (Source: {r.get('source_doc_id')})")
                            
        # Save assistant message to session state
        st.session_state.messages.append({"role": "assistant", "content": resp})

# --- TAB 2: JUDGE & ADMIN OPERATIONS ---
with tab_admin:
    st.subheader("⚙️ Judge & Admin Operations Hub")
    st.caption("Tools for live testing, document ingestion, viewing the Source Register, student records, and running the evaluation benchmark.")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "📥 Live Ingestion (POST /ingest)",
        "📑 Source Register (Annex B)",
        "👥 Student Records (Annex C)",
        "🔍 Audit Log (Annex D)",
        "📊 Evaluation Benchmark (Section 7)"
    ])
    
    # Ingestion Tab
    with admin_tab1:
        st.markdown("**Live Ingest New Document:**")
        with st.form("admin_ingest_form"):
            up_file = st.file_uploader("Document File (.txt, .md)", type=["txt", "md"])
            c_a, c_b = st.columns(2)
            with c_a:
                in_doc_id = st.text_input("Document ID", value="JDG-CIRCULAR-2026")
                in_title = st.text_input("Title", value="Notification Regarding Attendance Relaxation")
                in_issuer = st.text_input("Issuer", value="Office of the Dean Academics")
                in_auth = st.selectbox("Authority Level (1-5)", [1, 2, 3, 4, 5], index=1)
            with c_b:
                in_type = st.selectbox("Doc Type", ["circular", "regulation", "notice", "faq"])
                in_ver = st.text_input("Version", value="1.0")
                in_eff = st.date_input("Effective From", datetime(2026, 10, 1)).strftime("%Y-%m-%d")
                in_super = st.text_input("Supersedes (optional)", value="")
                
            submitted = st.form_submit_button("Ingest Document")
            if submitted and up_file:
                content_str = up_file.read().decode("utf-8", errors="replace")
                meta = {
                    "doc_id": in_doc_id, "title": in_title, "issuer": in_issuer,
                    "authority_level": in_auth, "doc_type": in_type, "version": in_ver,
                    "effective_from": in_eff, "supersedes": in_super,
                    "scope_programmes": "ALL", "scope_batches": "ALL",
                    "provenance": "Live Judge Upload", "retrieved_on": in_eff,
                    "synthetic": "N", "content": content_str
                }
                from core.database import insert_source_document
                from core.vector_store import index_document
                insert_source_document(meta)
                chunks_count = index_document(in_doc_id, in_title, content_str, meta)
                st.success(f"✅ Ingested `{in_doc_id}` successfully with {chunks_count} chunks indexed live!")
                
    # Source Register Tab
    with admin_tab2:
        import pandas as pd
        docs_list = get_source_register()
        if docs_list:
            df_docs = pd.DataFrame(docs_list)
            cols = ["doc_id", "title", "issuer", "authority_level", "doc_type", "version", "effective_from", "supersedes"]
            st.dataframe(df_docs[[c for c in cols if c in df_docs.columns]], use_container_width=True)
            
    # Student Records Tab
    with admin_tab3:
        import pandas as pd
        st.markdown("**Registered Students in SQLite:**")
        st.dataframe(pd.DataFrame(get_all_students()), use_container_width=True)
        
        st.markdown("**Rule Registry:**")
        st.dataframe(pd.DataFrame(get_all_rules()), use_container_width=True)
        
    # Audit Log Tab
    with admin_tab4:
        t_id = st.text_input("Enter Trace ID:")
        if st.button("Lookup Audit") and t_id:
            aud = get_audit_record(t_id.strip())
            if aud:
                st.json(aud)
            else:
                st.warning("Audit record not found.")
                
        st.divider()
        st.markdown("**Recent Audits:**")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT trace_id, timestamp, student_id, question, answer_type, latency_ms FROM audit_records ORDER BY timestamp DESC LIMIT 10")
            recent = [dict(r) for r in cur.fetchall()]
            if recent:
                st.dataframe(pd.DataFrame(recent), use_container_width=True)
                
    # Evaluation Benchmark Tab
    with admin_tab5:
        st.markdown("**Run Section 7 Benchmark Suite (20 Questions):**")
        if st.button("▶️ Execute Benchmark Suite", type="primary"):
            from evaluate import run_evaluation
            with st.spinner("Running 20 evaluation test cases..."):
                eval_file = "tests/eval_dataset.json"
                with open(eval_file) as f:
                    eval_data = json.load(f)
                    
                results = []
                correct = 0
                for case in eval_data:
                    res = ask_assistant(case["question"], case.get("student_id"), as_of_date_str)
                    act_type = res.get("answer_type")
                    exp_type = case["expected_answer_type"]
                    ok = (act_type == exp_type) or (exp_type == "conflict_flagged" and act_type in ["conflict_flagged", "retrieved_fact"])
                    if ok:
                        correct += 1
                    results.append({
                        "ID": case["id"],
                        "Question": case["question"][:55] + "...",
                        "Expected": exp_type,
                        "Actual": act_type,
                        "Status": "✅ PASS" if ok else "❌ FAIL"
                    })
                
                score_pct = round((correct / len(eval_data)) * 100, 1)
                st.metric("Benchmark Accuracy", f"{score_pct}%", f"{correct}/{len(eval_data)} Passed")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
