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
    return {"status": "online", "system": "RightsNavigator AI Backend", "version": "1.0.0"}

@router.get("/pincode/{pincode}")
async def pincode_lookup(pincode: str, locality: str = "", is_village: bool = False):
    if not pincode or len(pincode.strip()) < 3:
        raise HTTPException(status_code=400, detail="Invalid PIN code format")
    info = await lookup_pincode(pincode.strip(), locality.strip(), is_village)
    return info

@router.get("/locations/search")
async def location_search(q: str = Query(..., min_length=2, max_length=100)):
    return {"suggestions": await search_locations(q)}

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
