import json
import os
import httpx
import logging
from fastapi import HTTPException
from app.database import get_db_connection
from app.services.pincode_service import lookup_pincode
from app.services.rag import classify_and_retrieve, generate_grounded_response, generate_fallback_response

logger = logging.getLogger("navigator_engine")

ACTIVE_CATEGORIES = {
    "potholes_roads",
    "garbage_sanitation",
    "water_supply",
    "consumer_rights",
    "tenant_rights",
    "rti_access"
}

# Keyword matcher for quick fallback category detection
CATEGORY_KEYWORDS = {
    "potholes_roads": ["pothole", "road", "street", "asphalt", "tar", "accident", "divider", "traffic signal", "bridge", "highway", "footpath", "tarmac"],
    "garbage_sanitation": ["garbage", "trash", "waste", "sanitation", "dump", "smell", "drainage", "sewage", "toilet", "litter", "cleanliness", "swachh"],
    "water_supply": ["water", "tap", "pipeline", "leak", "contamination", "drinking water", "supply", "borewell", "tanker", "dirty water"],
    "consumer_rights": ["consumer", "refund", "defective", "product", "seller", "warranty", "overcharged", "e-commerce", "amazon", "flipkart", "shop", "guarantee"],
    "tenant_rights": ["tenant", "landlord", "rent", "deposit", "eviction", "lease", "flat", "house", "owner", "rent control", "maintenance"],
    "rti_access": ["rti", "right to information", "tender", "government file", "inspection", "public officer", "fund allocation", "pio", "delay"],
    "electricity_power": ["electricity", "power", "outage", "blackout", "meter", "current", "voltage", "discom", "bescom", "tata power", "transformer", "bill"],
    "healthcare_patient": ["health", "hospital", "doctor", "medical", "patient", "ambulance", "phc", "medicine", "treatment", "negligence", "admission", "cmo"],
    "labor_workplace": ["salary", "wage", "employer", "boss", "job", "pf", "epfo", "termination", "posh", "harassment", "overtime", "labour", "workplace"],
    "education_rte": ["school", "education", "rte", "college", "admission", "capitation fee", "mark sheet", "tc", "student", "teacher", "tuition"],
    "cyber_telecom": ["cyber", "scam", "fraud", "upi", "bank", "otp", "phishing", "sim", "telecom", "spam", "call drop", "trai", "1930"],
    "women_elder_rights": ["women", "domestic violence", "senior citizen", "elder", "maintenance", "pension", "abuse", "harassment", "ncw", "181", "elderline"],
    "real_estate_rera": ["builder", "rera", "possession", "flat booking", "apartment", "developer", "delay", "property", "registry", "landlord builder"]
}

async def generate_ai_navigation(query: str, loc_info: dict) -> dict | None:
    """Create tailored guidance from Gemini, using verified location context as guardrails."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    jurisdiction_type = loc_info.get("type", "Urban")
    local_body = loc_info.get("body", "Municipal Corporation")
    portal = loc_info.get("portal", "https://pgportal.gov.in/")
    helpline = loc_info.get("helpline", "1800-11-0001")
    district = loc_info.get("district", "")
    state = loc_info.get("state", "India")

    prompt = f"""You are RightsNavigator, a plain-language Indian civic-rights AI assistant. A citizen has described a problem. Your job is to:
1. Identify the governing statutory Act and relevant authority.
2. State the SLA (statutory response deadline in days).
3. Adapt advice to the citizen's exact jurisdiction: this citizen is in a {jurisdiction_type} area, served by {local_body} ({district}, {state}).
4. Give a step-by-step escalation roadmap with precise DOs and DON'Ts.
5. Mention the correct notice type to generate (RTI Sec 6, Consumer Court, Tenant Demand, Municipal Notice).

Citizen's problem: {query}
Verified jurisdiction: type={jurisdiction_type}, local body={local_body}, district={district}, state={state}, grievance portal={portal}, helpline={helpline}.

Return ONLY valid JSON — no markdown, no extra text — matching this exact schema:
{{"category_id":"one of potholes_roads,garbage_sanitation,water_supply,consumer_rights,tenant_rights,rti_access,electricity_power,healthcare_patient,labor_workplace,education_rte,cyber_telecom,women_elder_rights,real_estate_rera","category_title":"concise title for this specific issue","summary":"2-3 sentences explaining the citizen's rights specific to their situation and jurisdiction","applicable_rights":["right 1","right 2","right 3"],"act_name":"Primary governing Act or Rule (e.g. Consumer Protection Act 2019, RTI Act 2005, Solid Waste Management Rules 2016)","sla_days":7,"compensation_clause":"brief note on compensation or penalties if applicable, else empty string","notice_type":"one of rti_application,consumer_court_notice,tenant_deposit_demand,municipal_notice,labor_complaint,none","steps":[{{"step":1,"title":"Step title","detail":"Detailed actionable instruction specific to this problem and location"}},{{"step":2,"title":"Step title","detail":"Detailed actionable instruction"}},{{"step":3,"title":"Step title","detail":"Detailed actionable instruction including escalation path"}}],"dos":["DO specific action 1","DO specific action 2","DO specific action 3"],"donts":["DON'T specific warning 1","DON'T specific warning 2"]}}

Critical rules:
- Use plain, simple Indian English that any citizen can understand.
- Tailor EVERY field to the specific problem described — no generic templates.
- Do NOT invent statutory deadlines, compensation figures, or case-law citations.
- If there is danger to life, mention emergency contacts first.
- The local body, portal, and helpline above are the ONLY verified contacts — use them exactly as provided.
- Give exactly 3 steps, 2-4 dos, 2-3 don'ts."""
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.35,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json",
                        "thinkingConfig": {"thinkingBudget": 0},
                    },
                },
            )
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        guidance = json.loads(text)
        required = {"category_id", "category_title", "summary", "act_name", "sla_days", "compensation_clause", "steps", "dos", "donts"}
        # Models may provide additional useful steps despite the requested count.
        # Accept any complete roadmap instead of discarding a valid AI response.
        if not required.issubset(guidance) or not isinstance(guidance["steps"], list) or len(guidance["steps"]) < 3:
            logger.warning("Gemini response did not contain a complete navigation roadmap")
            return None

        category_id = guidance["category_id"]
        if category_id not in CATEGORY_KEYWORDS:
            category_id = "rti_access"

        return {
            "query": query,
            "category_id": category_id,
            "category_title": str(guidance["category_title"]),
            "summary": str(guidance["summary"]),
            "applicable_rights": [str(r) for r in guidance.get("applicable_rights", [])[:4]] if isinstance(guidance.get("applicable_rights"), list) else [],
            "location": {
                "pincode": loc_info["pincode"], "state": loc_info["state"],
                "district": loc_info["district"], "taluka": loc_info["taluka"],
                "type": loc_info["type"], "authority": loc_info["body"],
                "portal": loc_info["portal"], "helpline": loc_info["helpline"],
            },
            "act_name": str(guidance["act_name"]),
            "sla_days": max(1, min(int(guidance["sla_days"]), 365)),
            "compensation_clause": str(guidance["compensation_clause"]),
            "notice_type": str(guidance.get("notice_type", "none")),
            "steps": guidance["steps"],
            "dos": guidance["dos"],
            "donts": guidance["donts"],
            "action_buttons": [],
            "source": "gemini",
        }
    except (httpx.HTTPError, KeyError, ValueError, TypeError, json.JSONDecodeError, OverflowError) as exc:
        logger.warning("Gemini navigation generation failed: %s", exc)
        return None

async def analyze_citizen_problem(query: str, pincode: str = "560001") -> dict:
    # 1. Fetch location details
    loc_info = await lookup_pincode(pincode)
    user_state = loc_info.get("state", "all")

    # ── PRIMARY PATH: Gemini 2.5 Flash ──────────────────────────────────────
    # Gemini handles ALL categories — not just the 6 RAG-indexed ones.
    # It returns a structured JSON roadmap with steps, DOs, DON'Ts, SLA, act.
    gemini_result = await generate_ai_navigation(query, loc_info)

    if gemini_result:
        notice_type = gemini_result.get("notice_type", "none")
        NOTICE_LABELS = {
            "rti_application": ("draft_rti", "Generate RTI Application (Sec 6)", "FileText"),
            "consumer_court_notice": ("draft_consumer", "Generate Consumer Court Notice", "Scale"),
            "tenant_deposit_demand": ("draft_tenant", "Generate Tenant Deposit Demand Letter", "Home"),
            "municipal_notice": ("draft_notice", "Generate Municipal Grievance Notice", "Mail"),
            "labor_complaint": ("draft_labor", "Generate Labour Complaint Letter", "Briefcase"),
        }
        btn_id, btn_label, btn_icon = NOTICE_LABELS.get(notice_type, ("draft_notice", "Generate Legal/Grievance Notice", "Mail"))
        return {
            **gemini_result,
            "action_buttons": [
                {"id": btn_id, "label": btn_label, "icon": btn_icon},
                {
                    "id": "open_portal",
                    "label": "Visit Grievance Portal",
                    "url": loc_info.get("portal", "https://pgportal.gov.in/"),
                    "icon": "ExternalLink"
                }
            ],
            "grounded": True
        }

    # ── FALLBACK PATH: keyword match + static template ───────────────────────
    # Only reached if Gemini API key is missing or the call fails.
    query_lower = query.lower()

    matched_cat = "rti_access"  # safe default
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            matched_cat = cat
            break

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (matched_cat,))
    cat_row = cursor.fetchone()
    conn.close()

    is_rural = loc_info["type"] == "Rural"
    if cat_row:
        act_name = cat_row["act_name"]
        sla_days = cat_row["default_sla_days"]
        rules = json.loads(cat_row["rules_json"])
    else:
        act_name = "Indian Citizen Protection Acts"
        sla_days = 7
        rules = {}

    loc_key = "rural" if is_rural else "urban"
    specific_rule = rules.get(loc_key, {})
    target_authority = specific_rule.get("authority", loc_info["body"])
    portal_link = specific_rule.get("portal", loc_info["portal"])
    helpline = specific_rule.get("helpline", loc_info["helpline"])
    compensation_clause = specific_rule.get("compensation_clause", "")

    # Generic 3-step template
    steps = [
        {"step": 1, "title": "Document Your Issue", "detail": "Photograph or video the problem with timestamp and GPS enabled. Note exact location, date, and impact."},
        {"step": 2, "title": f"File Complaint with {target_authority}", "detail": f"Submit via {portal_link} or helpline {helpline}. Keep the complaint reference number."},
        {"step": 3, "title": f"Escalate if Unresolved in {sla_days} Days", "detail": "File an RTI under Section 6(1) RTI Act 2005 to inspect related government records if there is no action."}
    ]
    dos = ["DO keep copies of all evidence and complaint receipts.", "DO follow up in writing (email/post) to create a paper trail."]
    donts = ["DON'T pay unofficial fees or bribes to officials.", "DON'T close the complaint until the issue is physically resolved."]

    title = (cat_row["name"] if cat_row else matched_cat.replace("_", " ").title())
    summary = (
        f"Based on your description, this appears to relate to {title}. "
        f"The relevant authority is {target_authority}. "
        f"Under {act_name}, they are required to respond within {sla_days} days. "
        "Use the steps below to escalate your grievance effectively."
    )

    return {
        "query": query,
        "category_id": matched_cat,
        "category_title": title,
        "summary": summary,
        "applicable_rights": [
            f"Right to file a grievance with {target_authority}",
            "Right to request a written acknowledgement and reference number"
        ],
        "location": {
            "pincode": loc_info["pincode"], "state": loc_info["state"],
            "district": loc_info["district"], "taluka": loc_info["taluka"],
            "type": loc_info["type"], "authority": target_authority,
            "portal": portal_link, "helpline": helpline
        },
        "act_name": act_name,
        "sla_days": sla_days,
        "compensation_clause": compensation_clause,
        "steps": steps,
        "dos": dos,
        "donts": donts,
        "action_buttons": [
            {"id": "draft_notice", "label": "Generate Legal/Grievance Notice", "icon": "Mail"},
            {"id": "open_portal", "label": "Visit Grievance Portal", "url": "https://pgportal.gov.in/", "icon": "ExternalLink"}
        ],
        "grounded": False,
        "source": "keyword_fallback"
    }
