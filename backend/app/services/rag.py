import os
import logging
import sys
from supabase import create_client, Client
from groq import Groq

logger = logging.getLogger("rag_service")

# Map RAG categories to SQLite database category IDs
RAG_TO_DB_CATEGORY = {
    "pothole": "potholes_roads",
    "garbage": "garbage_sanitation",
    "water_supply": "water_supply",
    "tenant_rights": "tenant_rights",
    "rti": "rti_access",
    "consumer_protection": "consumer_rights"
}

_supabase = None
_model = None
_groq_client = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
        _supabase = create_client(url, key)
    return _supabase

def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Disable tokenizers warning
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in backend/.env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client

def hybrid_search(query: str, k: int = 8) -> list:
    """Perform hybrid search over Supabase Vector database and Full-Text Search.
    Combines and ranks results using Reciprocal Rank Fusion (RRF).
    """
    supabase = get_supabase()
    model = get_embedding_model()
    
    # 1. Generate query embedding
    query_embedding = model.encode(query).tolist()

    # 2. Vector search RPC
    vector_results = []
    try:
        res = supabase.rpc("match_statute_chunks", {"query_embedding": query_embedding, "match_count": k}).execute()
        vector_results = res.data or []
    except Exception as e:
        logger.error("Vector search failed: %s", e)

    # 3. Full-text search RPC
    fts_results = []
    try:
        res = supabase.rpc("fts_search_statute_chunks", {"query_text": query, "match_count": k}).execute()
        fts_results = res.data or []
    except Exception as e:
        logger.error("FTS search failed: %s", e)

    # 4. Reciprocal Rank Fusion (RRF) with constant k = 60
    rrf_scores = {}
    id_to_doc = {}

    for rank, doc in enumerate(vector_results, 1):
        doc_id = doc["id"]
        id_to_doc[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + rank))

    for rank, doc in enumerate(fts_results, 1):
        doc_id = doc["id"]
        id_to_doc[doc_id] = doc
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60.0 + rank))

    # Sort documents by RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    fused_docs = [id_to_doc[doc_id] for doc_id in sorted_ids[:k]]
    return fused_docs

def classify_and_retrieve(query: str, confidence_threshold: float = 0.4) -> dict:
    """Classify the user query category based on retrieved chunks confidence score.
    Returns classified category details or an unclear status.
    """
    fused_docs = hybrid_search(query, k=8)
    if not fused_docs:
        return {
            "status": "unclear",
            "message": "Could you add more detail about your issue?"
        }

    # Count frequencies of categories in top results
    top_category = fused_docs[0]["category"]
    same_cat_count = sum(1 for doc in fused_docs if doc["category"] == top_category)
    confidence = same_cat_count / len(fused_docs)

    db_category = RAG_TO_DB_CATEGORY.get(top_category)
    
    if confidence < confidence_threshold or not db_category:
        return {
            "status": "unclear",
            "message": "Could you add more detail about your issue?"
        }

    # Retrieve only chunks matching the resolved category
    matching_chunks = [doc for doc in fused_docs if doc["category"] == top_category]
    return {
        "status": "classified",
        "category": db_category,
        "chunks": matching_chunks,
        "confidence": confidence
    }

def generate_grounded_response(query: str, chunks: list, practical_info: dict) -> str:
    """Assemble RAG prompt and query Groq Llama-3.3-70b-versatile for grounded generation."""
    client = get_groq_client()
    
    # Format chunks and citations
    chunks_text = ""
    for idx, chunk in enumerate(chunks, 1):
        section_str = f", Section: {chunk['section']}" if chunk.get('section') else ""
        chunks_text += f"[{idx}] Act: {chunk['act_name']}{section_str}\nLegal Excerpt: {chunk['content']}\n\n"
        
    steps_text = ""
    for s in practical_info.get("steps", []):
        steps_text += f"- Step {s['step']}: {s['title']} - {s['detail']}\n"
        
    dos_text = "\n".join([f"- {d}" for d in practical_info.get("dos", [])])
    donts_text = "\n".join([f"- {d}" for d in practical_info.get("donts", [])])

    system_prompt = (
        "You are RightsNavigator, an expert civic-rights assistant in India. "
        "Strict Constraint: Base all legal claims and statutory rights ONLY on the provided legal excerpts. "
        "For every legal right, remedy, or claim you state, you MUST explicitly cite the Act and Section "
        "from the provided excerpts. If the resolution SLA is not explicitly stated in the legal excerpts, "
        "state that it is not defined in the excerpts rather than inventing or referencing external SLAs. "
        "Do not invent legal clauses, numbers, or details not found in the excerpts."
    )

    user_prompt = f"""Citizen Query: {query}

Verified Local Authority context:
- Authority: {practical_info.get('authority_name')}
- Grievance Portal: {practical_info.get('portal_url')}
- Helpline: {practical_info.get('helpline')}
- Compensation Clause: {practical_info.get('compensation_clause', 'None')}

Standard Escaped Steps:
{steps_text}

DOs (Gathering Evidence):
{dos_text}

DONTs (Practices to Avoid):
{donts_text}

Statutory Excerpts:
{chunks_text}

Generate a detailed 2-3 paragraph answer summarizing the citizen's rights under these acts, citing specific sections, and advising them on how to proceed. End with a clear action summary. Remember to maintain strict grounding constraint."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    return response.choices[0].message.content
