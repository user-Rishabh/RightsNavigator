from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import json
import uuid

from app.database import get_db_connection
from app.services.pincode_service import lookup_pincode, search_locations
from app.services.navigator_engine import analyze_citizen_problem
from app.services.document_generator import generate_rti_application, generate_legal_notice, generate_ai_draft

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    query: str
    pincode: Optional[str] = "560001"

class DraftRequest(BaseModel):
    doc_type: str # 'rti', 'consumer_notice', 'tenant_notice', 'municipal_complaint'
    citizen_name: Optional[str] = ""
    address: Optional[str] = ""
    pincode: Optional[str] = "560001"
    authority_name: Optional[str] = ""
    opponent_name: Optional[str] = ""
    subject: Optional[str] = ""
    details: Optional[str] = ""
    questions: Optional[List[str]] = []

class CaseCreateRequest(BaseModel):
    title: str
    category: str
    pincode: str
    location_type: str
    authority: str
    status: Optional[str] = "In Progress"
    details_json: Optional[dict] = {}

@router.get("/health")
def health_check():
    result = {}
    try:
        from app.services.rag import get_supabase
        supabase = get_supabase()
        
        # Test common RPC SQL executors
        for rpc_name in ["exec_sql", "run_sql", "execute_sql"]:
            try:
                res = supabase.rpc(rpc_name, {"query": "SELECT 1"}).execute()
                result[rpc_name] = {"status": "success", "data": res.data}
            except Exception as e1:
                try:
                    res = supabase.rpc(rpc_name, {"sql": "SELECT 1"}).execute()
                    result[rpc_name] = {"status": "success", "data": res.data}
                except Exception as e2:
                    result[rpc_name] = {"status": "failed", "error1": str(e1), "error2": str(e2)}
                    
        try:
            res = supabase.table("schemes").select("*").limit(1).execute()
            result["schemes_table_exists"] = True
            result["schemes_data"] = res.data
        except Exception as e_schemes:
            result["schemes_table_exists"] = False
            result["error_schemes"] = str(e_schemes)
            
    except Exception as e:
        result["error"] = str(e)
        
    return {"status": "online", "system": "RightsNavigator AI Backend", "version": "1.0.0", "db_status": result}

@router.get("/pincode/{pincode}")
async def pincode_lookup(pincode: str, locality: str = "", is_village: bool = False):
    if not pincode or len(pincode.strip()) < 3:
        raise HTTPException(status_code=400, detail="Invalid PIN code format")
    info = await lookup_pincode(pincode.strip(), locality.strip(), is_village)
    return info

@router.get("/locations/search")
async def location_search(q: str = Query(..., min_length=2, max_length=100)):
    return {"suggestions": await search_locations(q)}

@router.get("/locations/reverse-geocode")
async def reverse_geocode(lat: float, lon: float):
    import httpx
    import logging
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lon, "format": "jsonv2", "addressdetails": 1},
                headers={"User-Agent": "RightsNavigator/1.0 (civic location search)"}
            )
            if resp.status_code == 200:
                data = resp.json()
                address = data.get("address", {})
                pincode = address.get("postcode", "").split("-")[0].strip()
                if pincode and pincode.isdigit() and len(pincode) == 6:
                    name = address.get("suburb") or address.get("neighbourhood") or address.get("road") or address.get("city") or "Detected Area"
                    area_parts = []
                    for key in ("city", "town", "district", "state"):
                        val = address.get(key)
                        if val and val not in area_parts and val != name:
                            area_parts.append(val)
                    area = ", ".join(area_parts)
                    return {
                        "status": "success",
                        "pincode": pincode,
                        "name": name,
                        "area": area,
                        "is_village": bool(address.get("village") or address.get("hamlet"))
                    }
    except Exception as e:
        logging.warning("Reverse geocode failed: %s", e)
    
    raise HTTPException(status_code=400, detail="Could not resolve location. Please enter your PIN code manually.")

@router.post("/navigator/chat")
async def chat_navigator(req: ChatRequest):
    if not req.query or len(req.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty")
    analysis = await analyze_citizen_problem(req.query, req.pincode or "560001")
    return analysis

@router.get("/rights/categories")
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    rows = cursor.fetchall()
    conn.close()

    categories = []
    for r in rows:
        categories.append({
            "id": r["id"],
            "name": r["name"],
            "icon": r["icon"],
            "description": r["description"],
            "act_name": r["act_name"],
            "default_sla_days": r["default_sla_days"],
            "rules": json.loads(r["rules_json"])
        })
    return {"categories": categories}

@router.post("/generator/draft")
async def generate_draft(req: DraftRequest):
    if req.doc_type == "rti":
        text = generate_rti_application(
            citizen_name=req.citizen_name,
            address=req.address,
            pincode=req.pincode,
            authority_name=req.authority_name or "Public Information Officer",
            subject=req.subject,
            questions=req.questions
        )
    else:
        text = generate_legal_notice(
            doc_type=req.doc_type,
            citizen_name=req.citizen_name,
            address=req.address,
            opponent_name=req.opponent_name,
            details=req.details or req.subject,
            pincode=req.pincode,
            authority_name=req.authority_name
        )
    
    content, source = await generate_ai_draft(req.doc_type, text, req.details or req.subject, req.authority_name or req.opponent_name)
    return {
        "doc_type": req.doc_type,
        "title": f"Draft Document - {req.doc_type.upper()}",
        "content": content,
        "source": source
    }

@router.get("/cases")
def list_cases():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    cases = []
    for r in rows:
        cases.append({
            "id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "pincode": r["pincode"],
            "location_type": r["location_type"],
            "authority": r["authority"],
            "status": r["status"],
            "created_at": r["created_at"],
            "details": json.loads(r["details_json"]) if r["details_json"] else {}
        })
    return {"cases": cases}

@router.post("/cases")
def create_case(req: CaseCreateRequest):
    case_id = f"CASE-2026-{uuid.uuid4().hex[:4].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cases (id, title, category, pincode, location_type, authority, status, details_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (case_id, req.title, req.category, req.pincode, req.location_type, req.authority, req.status, json.dumps(req.details_json))
    )
    conn.commit()
    conn.close()
    return {"status": "created", "case_id": case_id}

class SchemeRecommendRequest(BaseModel):
    query: str
    profile: dict

def evaluate_eligibility(scheme: dict, profile: dict) -> dict:
    reasons = []
    status = "Not Eligible"
    score = 10
    
    state_filter = profile.get("state", "Karnataka")
    age = int(profile.get("age", 25))
    income = float(profile.get("income", 12000))
    occupation = profile.get("occupation", "Unorganized Worker")
    housing = profile.get("housing", "Tenant")
    bpl = profile.get("bpl", "No")
    gender = profile.get("gender", "Female")
    
    scheme_state = scheme.get("state", "All")
    if scheme_state != "All" and scheme_state.lower() != state_filter.lower():
        return {
            "status": "Not Eligible",
            "score": 5,
            "reasons": [f"This scheme is only active in {scheme_state}. Current state is {state_filter}."]
        }
        
    s_id = scheme.get("id", "")
    if s_id is None:
        s_id = ""
    s_id = s_id.lower()
    name_lower = scheme.get("name", "").lower()
    
    if "arogya" in name_lower or "pmjay" in s_id or "health insurance" in name_lower:
        is_unorg = occupation == "Unorganized Worker"
        is_low_inc = income <= 15000
        is_bpl = bpl == "Yes"
        is_kutcha = housing == "Homeless/Kutcha House"
        
        if is_low_inc or is_unorg or is_bpl or is_kutcha:
            status = "Eligible"
            score = 95
            if is_low_inc: reasons.append(f"Monthly income (₹{income:,.0f}) is below ₹15,000 limit.")
            if is_unorg: reasons.append("Working in unorganized sector (fits occupational criteria).")
            if is_bpl: reasons.append("Possess active BPL / Priority Ration Card status.")
            if is_kutcha: reasons.append("Residing in homeless / kutcha housing.")
        elif income <= 25000:
            status = "Possibly Eligible"
            score = 60
            reasons.append(f"Monthly income (₹{income:,.0f}) is under ₹25,000. Pending verification of SECC data.")
        else:
            reasons.append("Income exceeds threshold and no target occupational/deprivation criteria met.")
            
    elif "awas" in name_lower or "housing" in name_lower or "pmay" in s_id:
        is_low_inc = income <= 25000
        is_correct_housing = housing == "Tenant" or housing == "Homeless/Kutcha House"
        
        if is_low_inc and is_correct_housing:
            status = "Eligible"
            score = 95
            reasons.append("Income matches EWS/LIG threshold (below ₹25,000/month).")
            reasons.append("Do not own permanent pucca housing (currently Renting or Kutcha house).")
        elif income <= 50000:
            status = "Possibly Eligible"
            score = 60
            reasons.append("Income is under ₹50,000/month. Requires certificate verifying no ownership of other properties.")
        else:
            reasons.append("Income exceeds housing eligibility caps or user already owns a permanent house.")
            
    elif "maan-dhan" in name_lower or "pmsym" in s_id or "shram yogi" in name_lower:
        is_correct_age = age >= 18 and age <= 40
        is_unorg = occupation == "Unorganized Worker"
        is_correct_income = income <= 15000
        
        if is_correct_age and is_unorg and is_correct_income:
            status = "Eligible"
            score = 95
            reasons.append(f"Age is {age} (fits the required 18 to 40 entry bracket).")
            reasons.append("Active worker in the unorganized sector.")
            reasons.append(f"Monthly income (₹{income:,.0f}) is within the ₹15,000 threshold.")
        elif is_unorg and is_correct_income:
            status = "Possibly Eligible"
            score = 60
            reasons.append(f"Meets income and occupation criteria, but age ({age}) is outside the 18-40 enrolment window.")
        else:
            if not is_unorg: reasons.append("Scheme is exclusively for unorganized sector workers.")
            if not is_correct_age: reasons.append("Age is outside entry limit (18-40).")
            if not is_correct_income: reasons.append("Income exceeds unorganized worker cap of ₹15,000.")
            
    elif "kisan" in name_lower or "pmkisan" in s_id or "farmer" in name_lower:
        if occupation == "Farmer":
            status = "Eligible"
            score = 95
            reasons.append("Profile occupation matches active landholding farmer criteria.")
        elif occupation == "None" or occupation == "Unorganized Worker":
            status = "Possibly Eligible"
            score = 60
            reasons.append("Eligible if cultivable landholding documents (Khata/Patta) are registered in your name.")
        else:
            reasons.append("Non-agricultural worker. Cultivable agricultural landholding required.")
            
    elif "garib kalyan" in name_lower or "pmgkay" in s_id or "ration" in name_lower or "food security" in name_lower:
        is_bpl = bpl == "Yes"
        is_low_inc = income <= 10000
        
        if is_bpl or is_low_inc:
            status = "Eligible"
            score = 95
            if is_bpl: reasons.append("Possess Below Poverty Line (BPL) or priority household card.")
            if is_low_inc: reasons.append(f"Income (₹{income:,.0f}) is under BPL benchmark.")
        elif income <= 18000:
            status = "Possibly Eligible"
            score = 60
            reasons.append("Income is under ₹18,000. Requires registered NFSA Food Security Card.")
        else:
            reasons.append("Does not hold BPL status or registered NFSA food security card.")
            
    elif "sukanya" in name_lower or "ssy" in s_id:
        is_female = gender == "Female"
        is_kid = age <= 10
        
        if is_female and is_kid:
            status = "Eligible"
            score = 95
            reasons.append("Gender matches scheme beneficiary target (Female Child).")
            reasons.append(f"Child age ({age}) is under the 10-year limit.")
        elif is_female and age <= 18:
            status = "Possibly Eligible"
            score = 60
            reasons.append("Gender is Female. Eligible if account was opened prior to age 10.")
        else:
            if not is_female: reasons.append("SSY accounts are openable only for a girl child.")
            if not is_kid: reasons.append("Beneficiary opening age must be under 10 years.")
            
    elif "swanidhi" in name_lower or "pmsvanidhi" in s_id or "street vendor" in name_lower:
        is_unorg = occupation == "Unorganized Worker"
        is_low_inc = income <= 20000
        
        if is_unorg and is_low_inc:
            status = "Eligible"
            score = 95
            reasons.append("Working in unorganized sector (matches street vendor classification).")
            reasons.append(f"Monthly income (₹{income:,.0f}) is within the credit-assist limit.")
        elif is_unorg:
            status = "Possibly Eligible"
            score = 60
            reasons.append("Unorganized worker, but income is higher. Requires local vendor certificate (CoV) for verification.")
        else:
            reasons.append("Requires street vending ID card or Certificate of Vending from Municipal ULB.")
            
    elif "mudra" in name_lower or "self-employment" in name_lower:
        if occupation == "Business Owner":
            status = "Eligible"
            score = 95
            reasons.append("Profile matches micro-enterprise owner / business promoter.")
        elif occupation == "Unorganized Worker" or occupation == "None":
            status = "Possibly Eligible"
            score = 60
            reasons.append("Eligible for Shishu loan category to establish a new micro/small startup enterprise.")
        else:
            reasons.append("Excludes salaried employees. Must operate or propose a small trade, service, or manufacturing business.")
            
    elif "old age" in name_lower or "ignoaps" in s_id or "pension" in name_lower:
        is_senior = age >= 60
        is_bpl = bpl == "Yes"
        
        if is_senior and is_bpl:
            status = "Eligible"
            score = 95
            reasons.append(f"Age is {age} (elderly citizen ≥ 60 years criteria met).")
            reasons.append("Registered BPL household cardholder.")
        elif is_senior and income <= 15000:
            status = "Possibly Eligible"
            score = 60
            reasons.append(f"Age is {age}. Requires an official BPL state certification or local income check.")
        else:
            if not is_senior: reasons.append("Minimum pension age is 60 years.")
            if not is_bpl: reasons.append("Indigent criteria: BPL cardholder status required.")
            
    return {"status": status, "score": score, "reasons": reasons}

@router.get("/schemes")
def get_schemes():
    try:
        from app.services.rag import get_supabase
        supabase = get_supabase()
        
        # Auto-seed check for new 'schemes' table
        try:
            res_count = supabase.table("schemes").select("id").execute()
            count = len(res_count.data) if res_count.data else 0
            if count < 10:
                print("Seeding government schemes into Supabase 'schemes' table...")
                from scripts.seed_schemes import seed
                seed()
        except Exception as e_seed:
            print("Auto-seeding check failed on 'schemes' table:", e_seed)
            
        res = supabase.table("schemes").select("*").execute()
        rows = res.data or []
        
        if not rows:
            raise Exception("No rows returned from Supabase 'schemes' table")
            
        schemes = []
        for s in rows:
            docs = s.get("documents")
            if isinstance(docs, str):
                try:
                    docs = json.loads(docs)
                except Exception:
                    docs = [docs] if docs else []
            elif not isinstance(docs, list):
                docs = []
                
            schemes.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "ministry": s.get("ministry"),
                "category": s.get("category"),
                "description": s.get("description"),
                "benefit_amount": s.get("benefits", "N/A"),
                "benefit_type": s.get("benefit_type", "Subsidy"),
                "state_applicability": s.get("state", "All"),
                "official_portal": s.get("official_url", "https://india.gov.in"),
                "source_url": s.get("source_url", "https://india.gov.in"),
                "last_verified": s.get("last_verified", "2026-08-15"),
                "required_documents": docs,
                "application_process": s.get("application_process", "Apply online.")
            })
        return schemes
    except Exception as e:
        print("Fetch from Supabase schemes table failed, loading local schemes.json fallback:", e)
        import os
        schemes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schemes.json")
        try:
            with open(schemes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e_json:
            raise HTTPException(status_code=500, detail=f"Failed to load schemes: {str(e_json)}")

@router.post("/schemes/recommend")
def recommend_schemes(req: SchemeRecommendRequest):
    import os
    import json
    import traceback
    import math
    
    state_filter = req.profile.get("state", "Karnataka")
    
    try:
        from sentence_transformers import SentenceTransformer
        from groq import Groq
        from app.services.rag import get_supabase
        
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode(req.query).tolist()
        
        results = []
        # 1. Try pgvector match_schemes RPC
        try:
            supabase = get_supabase()
            res = supabase.rpc("match_schemes", {
                "query_embedding": query_embedding,
                "match_threshold": 0.10,
                "match_count": 15,
                "state_filter": state_filter
            }).execute()
            if res.data:
                for r in res.data:
                    r["similarity_score"] = r.get("similarity", 0.0)
                    results.append(r)
        except Exception as e_rpc:
            print("match_schemes RPC search failed, falling back to schemes table query:", e_rpc)
            
        # 2. Try fetching from 'schemes' table and calculating cosine similarity in memory
        if not results:
            try:
                supabase = get_supabase()
                res = supabase.table("schemes").select("*").execute()
                rows = res.data or []
                for row in rows:
                    row_state = row.get("state", "All")
                    if row_state != "All" and row_state.lower() != state_filter.lower():
                        continue
                    
                    emb_field = row.get("embedding")
                    if emb_field:
                        # Parse embedding list
                        if isinstance(emb_field, str):
                            try:
                                emb_list = json.loads(emb_field)
                            except Exception:
                                emb_list = []
                        else:
                            emb_list = emb_field
                            
                        if len(emb_list) == len(query_embedding):
                            # Cosine similarity
                            sumxx, sumyy, sumxy = 0, 0, 0
                            for i in range(len(query_embedding)):
                                x = query_embedding[i]
                                y = emb_list[i]
                                sumxx += x*x
                                sumyy += y*y
                                sumxy += x*y
                            score = 0.0
                            if sumxx > 0 and sumyy > 0:
                                score = sumxy / math.sqrt(sumxx * sumyy)
                            
                            row["similarity_score"] = score
                            results.append(row)
                results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
                results = results[:15]
            except Exception as e_table:
                print("schemes table query search failed, loading local schemes.json fallback:", e_table)
                
        # 3. Fallback to local schemes.json if database fetch failed completely
        if not results:
            schemes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schemes.json")
            with open(schemes_path, "r", encoding="utf-8") as f:
                local_schemes = json.load(f)
            for s in local_schemes:
                s_state = s.get("state_applicability", s.get("state", "All"))
                if s_state != "All" and s_state.lower() != state_filter.lower():
                    continue
                    
                embed_text = f"{s['name']}. {s['description']}. Eligibility: {s.get('detailed_eligibility', s.get('eligibility_criteria', ''))}"
                s_emb = model.encode(embed_text).tolist()
                
                sumxx, sumyy, sumxy = 0, 0, 0
                for i in range(len(query_embedding)):
                    x = query_embedding[i]
                    y = s_emb[i]
                    sumxx += x*x
                    sumyy += y*y
                    sumxy += x*y
                score = 0.0
                if sumxx > 0 and sumyy > 0:
                    score = sumxy / math.sqrt(sumxx * sumyy)
                    
                s_copy = dict(s)
                s_copy["state"] = s_state
                s_copy["benefits"] = s.get("benefit_amount", s.get("benefits", "N/A"))
                s_copy["eligibility_criteria"] = s.get("detailed_eligibility", s.get("eligibility_criteria", ""))
                s_copy["official_url"] = s.get("official_portal", s.get("official_url", "https://india.gov.in"))
                s_copy["source_url"] = s.get("source_url", "https://india.gov.in")
                s_copy["last_verified"] = s.get("last_verified", "2026-08-01")
                s_copy["similarity_score"] = score
                results.append(s_copy)
            results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
            results = results[:10]
            
        recommended_schemes = []
        for s in results:
            elig = evaluate_eligibility(s, req.profile)
            
            docs = s.get("documents", s.get("required_documents"))
            if isinstance(docs, str):
                try:
                    docs = json.loads(docs)
                except Exception:
                    docs = [docs] if docs else []
            elif not isinstance(docs, list):
                docs = []
                
            recommended_schemes.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "ministry": s.get("ministry"),
                "category": s.get("category"),
                "description": s.get("description"),
                "benefit_amount": s.get("benefits", s.get("benefit_amount", "N/A")),
                "benefit_type": s.get("benefit_type", "Subsidy"),
                "state_applicability": s.get("state", s.get("state_applicability", "All")),
                "official_portal": s.get("official_url", s.get("official_portal", "https://india.gov.in")),
                "source_url": s.get("source_url", "https://india.gov.in"),
                "last_verified": s.get("last_verified", "2026-08-01"),
                "required_documents": docs,
                "application_process": s.get("application_process", "Apply online at official portal."),
                "similarity_score": s.get("similarity_score", 0.0),
                "eligibility": elig
            })
            
        has_relevance = any(s["similarity_score"] >= 0.10 for s in recommended_schemes)
        
        if not recommended_schemes or not has_relevance:
            return {
                "grounded_response": "No relevant government scheme was found for your problem.",
                "recommended_schemes": []
            }
            
        # Compile retrieved schemes context for the LLM
        context_items = []
        for idx, s in enumerate(recommended_schemes[:5], 1):
            context_items.append(
                f"Scheme {idx}: {s['name']}\n"
                f"Ministry: {s['ministry']}\n"
                f"Category: {s['category']}\n"
                f"State: {s['state_applicability']}\n"
                f"Benefits: {s['benefit_amount']}\n"
                f"Eligibility Criteria: {s['eligibility']['reasons']}\n"
                f"Required Documents: {', '.join(s['required_documents'])}\n"
                f"Official Link: {s['official_portal']}\n"
            )
        context = "\n---\n".join(context_items)
        
        profile_desc = f"State: {state_filter}, Age: {req.profile.get('age')}, Income: {req.profile.get('income')}, Occupation: {req.profile.get('occupation')}, Housing: {req.profile.get('housing')}, BPL: {req.profile.get('bpl')}, Gender: {req.profile.get('gender')}."
        
        prompt = f"""You are a government scheme recommendation assistant.
Generate a clear, grounded response recommendation based ONLY on the retrieved schemes database context below.

Citizen Profile:
{profile_desc}

Citizen's Problem Statement:
"{req.query}"

Retrieved Schemes Knowledge Base:
{context}

Guidelines:
1. Recommend ONLY schemes present in the retrieved knowledge base.
2. Explain clearly WHY each recommended scheme matches.
3. Compare profile with criteria, stating Eligible, Possibly Eligible, or Not Eligible.
4. List benefits, required documents, and application process.
5. Provide the exact Official Link for each scheme.
6. If none are relevant, respond exactly with: "No relevant government scheme was found for your problem."

Format the response in structured Markdown with clean headings (using ###) and bullet points. DO NOT use markdown tables under any circumstances. Bold key terms (using **) for emphasis.
"""
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        
        chat_completion = None
        model_errors = []
        # Modern active models on Groq:
        active_models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "groq/compound",
            "groq/compound-mini"
        ]
        for current_model in active_models:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=current_model,
                    temperature=0.2,
                    max_tokens=2000
                )
                break
            except Exception as e_model:
                model_errors.append(f"{current_model}: {str(e_model)}")
                continue
                
        if not chat_completion:
            try:
                available_models = [m.id for m in client.models.list().data]
            except Exception as e_models:
                available_models = [str(e_models)]
            raise Exception(f"All Groq models failed to respond. Available models: {available_models}. Details: {', '.join(model_errors)}")
            
        grounded_resp = chat_completion.choices[0].message.content
        
        return {
            "grounded_response": grounded_resp,
            "recommended_schemes": recommended_schemes
        }
    except Exception as e:
        return {
            "grounded_response": f"### Python RAG Service Error\n```\n{str(e)}\n{traceback.format_exc()}\n```",
            "recommended_schemes": []
        }


@router.get("/test-supabase")
def test_supabase():
    import os
    from supabase import create_client
    result = {}
    try:
        result["env_keys"] = list(os.environ.keys())
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)
        try:
            res = supabase.table("government_schemes").select("*").limit(1).execute()
            result["government_schemes_exists"] = True
            result["sample_data"] = res.data
        except Exception as e_schemes:
            result["government_schemes_exists"] = False
            result["error_schemes"] = str(e_schemes)
    except Exception as e:
        result["error"] = str(e)
    return result
