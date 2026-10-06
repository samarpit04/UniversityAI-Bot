import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from core.config import settings
from core.database import get_source_register

# Create ChromaDB client
_client = None
_collection = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    return _client

def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        # Use sentence-transformers embedding function or chromadb default
        try:
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL_NAME
            )
        except Exception:
            emb_fn = embedding_functions.DefaultEmbeddingFunction()
            
        _collection = client.get_or_create_collection(
            name="university_documents",
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def chunk_document_by_clauses(doc_id: str, title: str, content: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits text by structural sections/clauses (e.g., Clause 11.2, Part A, Section 3).
    Ensures judges get precise section and page references.
    """
    chunks = []
    lines = content.strip().split("\n")
    
    current_section = "General"
    current_page = "1"
    current_text = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Check for page markers
        page_match = re.search(r"Page\s*(\d+)", stripped, re.IGNORECASE)
        if page_match:
            current_page = page_match.group(1)
            
        # Check for section or clause headers
        section_match = re.match(r"^(Section\s+\d+(\.\d+)?|Clause\s+\d+(\.\d+)?|Part\s+[A-G]|Q:|\d+\.\d+)", stripped, re.IGNORECASE)
        if section_match:
            if current_text:
                chunk_body = "\n".join(current_text)
                chunks.append({
                    "text": f"[{title} - {current_section}]\n{chunk_body}",
                    "section": current_section,
                    "page": current_page,
                    "doc_id": doc_id,
                    "title": title
                })
                current_text = []
            current_section = stripped[:60]
            
        current_text.append(stripped)
        
    if current_text:
        chunk_body = "\n".join(current_text)
        chunks.append({
            "text": f"[{title} - {current_section}]\n{chunk_body}",
            "section": current_section,
            "page": current_page,
            "doc_id": doc_id,
            "title": title
        })
        
    # If no section-based chunks were created, fallback to paragraph chunking
    if not chunks and content.strip():
        chunks.append({
            "text": content.strip(),
            "section": "General",
            "page": "1",
            "doc_id": doc_id,
            "title": title
        })
        
    return chunks

def index_document(doc_id: str, title: str, content: str, metadata: Dict[str, Any]) -> int:
    """
    Indexes or re-indexes a document in ChromaDB.
    Supports live ingestion via POST /ingest.
    """
    collection = get_collection()
    
    # Delete existing entries for this doc_id
    try:
        existing = collection.get(where={"doc_id": doc_id})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
    except Exception:
        pass
        
    chunks = chunk_document_by_clauses(doc_id, title, content, metadata)
    if not chunks:
        return 0
        
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = []
    
    for c in chunks:
        metadatas.append({
            "doc_id": doc_id,
            "title": title,
            "section": c["section"],
            "page": c["page"],
            "version": str(metadata.get("version", "1.0")),
            "effective_from": str(metadata.get("effective_from", "2024-07-01")),
            "effective_to": str(metadata.get("effective_to", "")),
            "authority_level": int(metadata.get("authority_level", 1)),
            "supersedes": str(metadata.get("supersedes", "")),
            "scope_programmes": str(metadata.get("scope_programmes", "ALL")),
            "scope_batches": str(metadata.get("scope_batches", "ALL")),
            "synthetic": str(metadata.get("synthetic", "N"))
        })
        
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    return len(chunks)

def query_vector_store(query_text: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    collection = get_collection()
    if collection.count() == 0:
        return []
        
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
            where=where
        )
    except Exception:
        # Retry without where clause if where filtering failed
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count())
        )
        
    retrieved = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
        
        for doc_text, meta, dist in zip(docs, metas, distances):
            retrieved.append({
                "text": doc_text,
                "doc_id": meta.get("doc_id", "UNKNOWN"),
                "title": meta.get("title", ""),
                "section": meta.get("section", "General"),
                "page": meta.get("page", "1"),
                "version": meta.get("version", "1.0"),
                "effective_from": meta.get("effective_from", ""),
                "effective_to": meta.get("effective_to", ""),
                "authority_level": int(meta.get("authority_level", 1)),
                "supersedes": meta.get("supersedes", ""),
                "scope_programmes": meta.get("scope_programmes", "ALL"),
                "scope_batches": meta.get("scope_batches", "ALL"),
                "score": round(1.0 - float(dist), 4) if dist is not None else 0.85
            })
    return retrieved

def initialize_vector_store():
    """
    Checks if ChromaDB contains docs. If not, ingests all docs from SQLite source register.
    """
    collection = get_collection()
    if collection.count() == 0:
        docs = get_source_register()
        for d in docs:
            index_document(
                doc_id=d["doc_id"],
                title=d["title"],
                content=d.get("content", ""),
                metadata=d
            )
        print(f"Vector store initialized with {collection.count()} chunks.")
