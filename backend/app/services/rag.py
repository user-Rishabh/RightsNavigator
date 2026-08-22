import os
import logging
import math
import json
from supabase import create_client, Client
from groq import Groq

logger = logging.getLogger("rag_service")

# Cache for singleton instances
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
        # Disable tokenizers parallel warning
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

def get_embedding_list(emb):
    if isinstance(emb, str):
        try:
            return json.loads(emb)
        except Exception:
            return []
    elif isinstance(emb, list):
        return emb
    return []

def cosine_similarity(v1, v2):
    sumxx, sumyy, sumxy = 0, 0, 0
    for i in range(len(v1)):
        x = v1[i]
        y = v2[i]
        sumxx += x*x
        sumyy += y*y
        sumxy += x*y
    if sumxx == 0 or sumyy == 0:
        return 0.0
    return sumxy / math.sqrt(sumxx * sumyy)

def hybrid_search_schemes(query: str, state_filter: str, k: int = 15) -> list:
    """Retrieve schemes matching user query, with robust postgres RPC and Python cosine-similarity fallback.
    """
    supabase = get_supabase()
    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()
    
    # 1. Try pgvector RPC
    try:
        res = supabase.rpc("match_government_schemes", {
            "query_embedding": query_embedding,
            "match_threshold": 0.25,
            "match_count": k,
            "state_filter": state_filter
        }).execute()
        if res.data:
            for r in res.data:
                r["similarity_score"] = r.get("similarity", 0.0)
            return res.data
    except Exception as e:
        logger.warning("Supabase match_government_schemes RPC failed, falling back to local Python cosine similarity: %s", e)

    # 2. Local Fallback: Fetch matching states and calculate similarity in memory
    try:
        res = supabase.table("government_schemes").select("*").execute()
        rows = res.data or []
        
        matched_results = []
        for row in rows:
            # Check state applicability
            state_val = row.get("state", "All")
            if state_val != "All" and state_val.lower() != state_filter.lower():
                continue
                
            emb_field = row.get("embedding")
            if emb_field:
                emb_list = get_embedding_list(emb_field)
                if len(emb_list) == len(query_embedding):
                    score = cosine_similarity(query_embedding, emb_list)
                    row["similarity_score"] = score
                    matched_results.append(row)
                    
        # Sort by similarity score descending
        matched_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matched_results[:k]
    except Exception as ex:
        logger.error("All database search methods failed for schemes, falling back to local schemes.json: %s", ex)
        try:
            import os
            schemes_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "schemes.json")
            if not os.path.exists(schemes_path):
                # Try relative to the app folder
                schemes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schemes.json")
                
            with open(schemes_path, "r", encoding="utf-8") as f:
                local_schemes = json.load(f)
            
            matched_results = []
            for s in local_schemes:
                state_val = s.get("state_applicability", s.get("state", "All"))
                if state_val != "All" and state_val.lower() != state_filter.lower():
                    continue
                
                embed_text = f"{s['name']}. {s['description']}. Eligibility: {s.get('detailed_eligibility', s.get('eligibility_criteria', ''))}"
                emb_list = model.encode(embed_text).tolist()
                
                score = cosine_similarity(query_embedding, emb_list)
                
                s_copy = dict(s)
                s_copy["state"] = state_val
                s_copy["benefits"] = s.get("benefit_amount", s.get("benefits", "N/A"))
                s_copy["eligibility_criteria"] = s.get("detailed_eligibility", s.get("eligibility_criteria", ""))
                s_copy["official_url"] = s.get("official_portal", s.get("official_url", "https://india.gov.in"))
                s_copy["source_url"] = s.get("source_url", "https://india.gov.in")
                s_copy["last_verified"] = s.get("last_verified", "2026-08-01")
                s_copy["similarity_score"] = score
                matched_results.append(s_copy)
                
            matched_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return matched_results[:k]
        except Exception as e_json:
            logger.error("Local schemes.json fallback failed: %s", e_json)
            return []

def generate_grounded_response(query: str, schemes: list, user_profile: dict) -> str:
    """Use Groq Llama3 model to generate a grounded, natural-language recommendation response.
    """
    if not schemes:
        return "No relevant government scheme was found for your problem."

    # Format the schemes context for the LLM
    context_items = []
    for idx, s in enumerate(schemes, 1):
        context_items.append(
            f"Scheme {idx}: {s['name']}\n"
            f"Ministry: {s['ministry']}\n"
            f"Category: {s['category']}\n"
            f"State: {s.get('state', 'All')}\n"
            f"Benefits: {s.get('benefits', s.get('benefit_amount', 'N/A'))}\n"
            f"Eligibility Criteria: {s['eligibility_criteria']}\n"
            f"Required Documents: {', '.join(s['required_documents']) if isinstance(s['required_documents'], list) else s['required_documents']}\n"
            f"Application Process: {s['application_process']}\n"
            f"Official Link: {s.get('official_url', s.get('official_portal', 'https://india.gov.in'))}\n"
            f"Source URL: {s.get('source_url', 'https://india.gov.in')}\n"
            f"Last Verified: {s['last_verified']}\n"
        )
    context = "\n---\n".join(context_items)

    profile_desc = (
        f"State: {user_profile.get('state', 'N/A')}, "
        f"Age: {user_profile.get('age', 'N/A')} years, "
        f"Monthly Income: ₹{user_profile.get('income', 'N/A')}, "
        f"Occupation: {user_profile.get('occupation', 'N/A')}, "
        f"Housing Type: {user_profile.get('housing', 'N/A')}, "
        f"BPL Card: {user_profile.get('bpl', 'N/A')}, "
        f"Gender: {user_profile.get('gender', 'N/A')}."
    )

    prompt = f"""You are a government scheme recommendation assistant.
Generate a clear, grounded response recommendation based ONLY on the retrieved schemes database context below.

Citizen Profile:
{profile_desc}

Citizen's Problem Statement:
"{query}"

Retrieved Schemes Knowledge Base:
{context}

Guidelines:
1. Recommend ONLY schemes present in the retrieved knowledge base that match the query semantically.
2. Explain clearly WHY each recommended scheme matches their situation.
3. Compare the citizen's profile with the eligibility criteria, stating whether they are Eligible, Possibly Eligible, or Not Eligible.
4. List the estimated benefits, required documents, and step-by-step application process for each recommendation.
5. Provide the exact Official Link and Source URL for each scheme. Do not modify or invent URLs.
6. Do NOT invent or assume any details. If required details (like exact landholding or caste) are missing from the profile, state that they are 'Possibly Eligible' and highlight what verification is needed.
7. If none of the retrieved schemes are relevant, respond exactly with: "No relevant government scheme was found for your problem."

Format the response in structured, readable Markdown with clear headings for each scheme.
"""

    try:
        client = get_groq_client()
        # Use llama3-70b-8192 for high-quality reasoning, fallback to llama3-8b-8192 if needed
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.2,
            max_tokens=2500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error("Groq completions failed, trying fallback model: %s", e)
        try:
            client = get_groq_client()
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.2,
                max_tokens=2500
            )
            return chat_completion.choices[0].message.content
        except Exception as e_inner:
            logger.error("All LLM generation failed: %s", e_inner)
            return "Failed to generate AI response due to API connection issue. Please review the recommended scheme cards below."
