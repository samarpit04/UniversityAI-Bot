from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except Exception:
        return None

def apply_precedence_policy(
    retrieved_chunks: List[Dict[str, Any]],
    as_of_date_str: str,
    student_programme: Optional[str] = None,
    student_batch: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """
    Implements Annex A - Source Precedence Policy:
    Returns:
    (valid_chunks, overruled_chunks, upcoming_chunks, precedence_explanation)
    """
    as_of_date = parse_date(as_of_date_str) or datetime.now()
    
    applicable_chunks = []
    upcoming_chunks = []
    
    # 1. Applicability Filter
    for chunk in retrieved_chunks:
        eff_from = parse_date(chunk.get("effective_from", ""))
        eff_to = parse_date(chunk.get("effective_to", ""))
        
        # Check future documents
        if eff_from and eff_from > as_of_date:
            upcoming_chunks.append(chunk)
            continue
            
        # Check expired documents
        if eff_to and eff_to < as_of_date:
            continue
            
        # Check Programme Scope
        scope_prog = chunk.get("scope_programmes", "ALL")
        if scope_prog != "ALL" and student_programme and student_programme not in scope_prog:
            continue
            
        # Check Batch Scope
        scope_batch = str(chunk.get("scope_batches", "ALL"))
        if scope_batch != "ALL" and student_batch:
            if scope_batch.endswith("+"):
                base_year = int(scope_batch[:-1])
                if student_batch < base_year:
                    continue
            elif str(student_batch) not in scope_batch:
                continue
                
        applicable_chunks.append(chunk)

    if not applicable_chunks:
        return [], [], upcoming_chunks, "No applicable documents found for the given as_of_date."

    # 2. Check Explicit Supersession
    # Map of superseded targets
    superseded_targets = {}
    for chunk in applicable_chunks:
        auth = chunk.get("authority_level", 5)
        supersedes = chunk.get("supersedes", "")
        if auth in (1, 2) and supersedes:
            # Targets can be doc_id or doc_id#clause
            for target in supersedes.split(";"):
                target = target.strip()
                if target:
                    superseded_targets[target] = chunk["doc_id"]

    valid_chunks = []
    overruled_chunks = []
    precedence_notes = []

    for chunk in applicable_chunks:
        doc_id = chunk["doc_id"]
        section = chunk.get("section", "")
        doc_clause = f"{doc_id}#{section}"
        
        # Check if superseded
        if doc_id in superseded_targets or doc_clause in superseded_targets:
            replacer = superseded_targets.get(doc_id) or superseded_targets.get(doc_clause)
            chunk["overruled_by"] = replacer
            chunk["overruled_reason"] = f"Explicitly superseded by {replacer}"
            overruled_chunks.append(chunk)
            precedence_notes.append(f"Document {doc_id} was superseded by {replacer} per Step 2 (Explicit Supersession).")
            continue
            
        valid_chunks.append(chunk)

    # 3. Authority and 4. Recency Sorting
    # Sort valid chunks by authority (lower number = higher authority)
    # Then by effective_from descending (newer = higher precedence)
    def sort_key(c):
        auth = c.get("authority_level", 5)
        eff = parse_date(c.get("effective_from", "")) or datetime(1970, 1, 1)
        return (auth, -eff.timestamp())

    valid_chunks.sort(key=sort_key)

    # Check for Level 5 (untrusted)
    for c in valid_chunks:
        if c.get("authority_level", 5) == 5:
            c["is_informational_only"] = True

    # 5. Build Explanation
    explanation_parts = []
    if precedence_notes:
        explanation_parts.extend(precedence_notes)
        
    if valid_chunks:
        top_auth = valid_chunks[0].get("authority_level", 1)
        top_doc = valid_chunks[0].get("title", valid_chunks[0].get("doc_id"))
        explanation_parts.append(f"Applied highest authority document: '{top_doc}' (Level {top_auth}) as of {as_of_date_str}.")

    explanation = " ".join(explanation_parts)
    return valid_chunks, overruled_chunks, upcoming_chunks, explanation
