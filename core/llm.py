import json
from typing import Dict, Any, List, Optional, Tuple
from huggingface_hub import InferenceClient
from core.config import settings

_client = None

def get_inference_client() -> Optional[InferenceClient]:
    global _client
    if _client is None:
        token = settings.HUGGINGFACE_ACCESS_TOKEN
        if token:
            _client = InferenceClient(token=token)
    return _client

SYSTEM_PROMPT = """You are the official AI-Powered University Student Services Assistant for Netaji Subhas University of Technology (NSUT), Delhi.

Your role is to assist students with academic regulations, attendance criteria, examination rules, and eligibility queries.

CRITICAL OPERATIONAL RULES:
1. GROUNDED IN EVIDENCE: Use ONLY the provided University Document Clauses and Deterministic Tool Results. Do NOT use general external knowledge or fabricate policies.
2. DETERMINISTIC TOOLS: If calculation/eligibility tool results are provided, treat them as 100% authoritative. DO NOT recalculate or contradict the tool's numbers or decisions.
3. ABSTENTION (R3): If the information is not found in the provided facts, say EXACTLY: "I could not find this information in the authorised university sources."
4. PRIVACY (R7): Never disclose data belonging to another student.
5. CITATIONS: State the exact document title and clause/section supporting your answer.
6. FORMAT: Respond clearly, politely, and professionally in GitHub markdown with bullet points and bold highlights.
"""

def call_huggingface_llm(
    question: str,
    context_chunks: List[Dict[str, Any]],
    tools_invoked: List[Dict[str, Any]],
    applied_rules: List[Dict[str, Any]],
    fallback_text: str = ""
) -> Tuple[str, str, int]:
    """
    Calls Hugging Face LLM (Llama-3.1-8B-Instruct or Qwen-2.5) to synthesize the grounded answer.
    Returns: (answer_text, model_name, estimated_tokens)
    """
    client = get_inference_client()
    if not client or settings.MOCK_LLM:
        return fallback_text, "deterministic-grounded", 0

    # Build prompt context
    doc_context_text = ""
    if context_chunks:
        doc_context_text = "### AUTHORIZED UNIVERSITY REGULATIONS & CIRCULARS:\n"
        for idx, c in enumerate(context_chunks[:3], 1):
            doc_context_text += f"{idx}. [{c.get('title')} - {c.get('section')}] (v{c.get('version')}, Eff: {c.get('effective_from')})\n{c.get('text', '')}\n\n"

    tools_text = ""
    if tools_invoked:
        tools_text = "### DETERMINISTIC TOOL RESULTS (FROM DATABASE):\n"
        for t in tools_invoked:
            tools_text += f"• Tool '{t.get('tool')}': {json.dumps(t.get('output', {}), indent=2)}\n\n"

    rules_text = ""
    if applied_rules:
        rules_text = "### APPLIED RULES (RULE REGISTRY):\n"
        for r in applied_rules:
            rules_text += f"• Rule {r.get('rule_id')}: threshold {r.get('value')} (Source: {r.get('source_doc_id')} {r.get('section', '')})\n"

    user_message = f"""STUDENT QUESTION:
{question}

{doc_context_text}
{tools_text}
{rules_text}

Synthesize a clear, authoritative, and helpful answer for the student adhering to the rules above. State relevant citations clearly."""

    models_to_try = [
        settings.HF_MODEL,
        "Qwen/Qwen2.5-72B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct"
    ]

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.1
            )
            ans = response.choices[0].message.content.strip()
            if ans:
                return ans, model_name, 250
        except Exception as e:
            continue

    # Fallback if network or rate limit occurred
    return fallback_text, "fallback-grounded", 0
