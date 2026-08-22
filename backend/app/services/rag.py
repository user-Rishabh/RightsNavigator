import os
import logging
import math
import json
import sys
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer

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

def classify_and_retrieve(query: str, user_state: str, confidence_threshold: float = 0.4) -> dict:
    """Classify the user query category based on retrieved chunks confidence score and filter by user state.
    Returns grounded category details, fallback category details, or an unclear status.
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

    # Group all votes matching this category
    category_votes = [doc for doc in fused_docs if doc["category"] == top_category]

    # Filter chunks relevant to this user's state (case-insensitive check)
    state_matched = []
    for c in category_votes:
        states = c.get("applicable_states", ["all"])
        # Normalize to lowercase for robust matching
        states_lower = [s.lower().strip() for s in states]
        if user_state.lower().strip() in states_lower or "all" in states_lower:
            state_matched.append(c)

    if state_matched:
        return {
            "status": "grounded",
            "category": db_category,
            "chunks": state_matched,
            "confidence": confidence
        }
    else:
        # Category exists, has chunks, but none match this user's state -> fallback
        return {
            "status": "fallback",
            "category": db_category,
            "confidence": confidence
        }

FALLBACK_PROMPT = """
You are giving GENERAL civic guidance, not verified against {user_state}'s specific municipal law. Do not cite a specific act or section number - we have not verified one for this state. Do not state a specific numeric SLA/deadline - say response times vary by local authority.

Citizen's situation: "{query}"
Category: {category}

Give a general, honest overview: likely responsible authority type (e.g. "your city's municipal corporation" or "state water board"), general steps to file a grievance (e.g. document the issue, check for the municipal corporation's online grievance portal, follow up with a written complaint), and clearly state this is general guidance - recommend the user check their municipal corporation's website for the exact process.
"""

def generate_fallback_response(query: str, category: str, user_state: str) -> str:
    """Generate ungrounded fallback guidance for categories that don't match the user's state."""
    client = get_groq_client()
    prompt = FALLBACK_PROMPT.format(query=query, category=category, user_state=user_state)
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    answer = completion.choices[0].message.content
    # Clean asterisks from fallback response
    return answer.replace("**", "").replace("*", "")

def generate_grounded_response(query: str, chunks: list, practical_info: dict) -> str:
    """Assemble RAG prompt and query Groq openai/gpt-oss-120b for grounded generation."""
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
        "Do not invent legal clauses, numbers, or details not found in the excerpts. "
        "Do not use markdown formatting in your response - no asterisks, no double asterisks, no bullet points, no headers. Write in plain prose sentences only, organized into short paragraphs."
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

    # Generate grounded response using Groq
    print("=== DEBUG RETRIEVED CHUNKS ===")
    for c in chunks:
        print(f"Category: {c.get('category')}, Act: {c.get('act_name')}, Section: {c.get('section')}")
        print(f"Content: {c.get('content')}")
        print("-" * 40)
    print("=== DEBUG FINAL PROMPT ===")
    print(f"System Prompt:\n{system_prompt}\n")
    print(f"User Prompt:\n{user_prompt}\n")
    print("==========================")

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    answer = response.choices[0].message.content
    # Foolproof cleanup of markdown asterisks
    return answer.replace("**", "").replace("*", "")
