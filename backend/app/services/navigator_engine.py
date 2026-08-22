import json
import os
import httpx
import logging
from fastapi import HTTPException
from app.database import get_db_connection
from app.services.pincode_service import lookup_pincode
from app.services.rag import classify_and_retrieve, generate_grounded_response

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

    prompt = f"""You are RightsNavigator, an Indian civic-rights assistant. Give tailored, practical guidance for the citizen's exact situation, rather than a generic template.

Citizen's message: {query}
Verified location context: district={loc_info['district']}, state={loc_info['state']}, jurisdiction={loc_info['type']}, local body={loc_info['body']}, grievance channel={loc_info['portal']}, helpline={loc_info['helpline']}.

Return ONLY valid JSON with this exact schema:
{{"category_id":"one of potholes_roads,garbage_sanitation,water_supply,consumer_rights,tenant_rights,rti_access,electricity_power,healthcare_patient,labor_workplace,education_rte,cyber_telecom,women_elder_rights,real_estate_rera","category_title":"short tailored title","summary":"2-3 sentence answer specific to the message","applicable_rights":["specific practical right 1","specific practical right 2"],"act_name":"relevant law/rule, or General civic grievance guidance if uncertain","sla_days":7,"compensation_clause":"short cautious note or empty string","steps":[{{"step":1,"title":"...","detail":"..."}},{{"step":2,"title":"...","detail":"..."}},{{"step":3,"title":"...","detail":"..."}}],"dos":["...","..."],"donts":["...","..."]}}

Rules: Use plain Indian English. Adapt advice to the stated incident. Do not invent dates, evidence, authorities, legal sections, compensation amounts, or statutory deadlines. Mention emergency services if there is immediate danger or injury. Give exactly 3 steps, 2-4 dos, and 2-4 don'ts. The provided local body and grievance channel are the only verified local contacts; do not replace them."""
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
            "applicable_rights": [str(right) for right in guidance.get("applicable_rights", [])[:4]] if isinstance(guidance.get("applicable_rights", []), list) else [],
            "location": {
                "pincode": loc_info["pincode"], "state": loc_info["state"],
                "district": loc_info["district"], "taluka": loc_info["taluka"],
                "type": loc_info["type"], "authority": loc_info["body"],
                "portal": loc_info["portal"], "helpline": loc_info["helpline"],
            },
            "act_name": str(guidance["act_name"]),
            "sla_days": max(1, min(int(guidance["sla_days"]), 365)),
            "compensation_clause": str(guidance["compensation_clause"]),
            "steps": guidance["steps"], "dos": guidance["dos"], "donts": guidance["donts"],
            "action_buttons": [], "source": "gemini",
        }
    except (httpx.HTTPError, KeyError, ValueError, TypeError, json.JSONDecodeError, OverflowError) as exc:
        logger.warning("Gemini navigation generation failed: %s", exc)
        return None

async def analyze_citizen_problem(query: str, pincode: str = "560001") -> dict:
    query_lower = query.lower()
    
    # 1. Fetch location details
    loc_info = await lookup_pincode(pincode)
    is_rural = loc_info["type"] == "Rural"

    # Use RAG-based classification and retrieval
    result = classify_and_retrieve(query)
    if result["status"] == "unclear":
        raise HTTPException(status_code=400, detail=result["message"])

    matched_cat = result["category"]
    chunks = result["chunks"]

    if matched_cat not in ACTIVE_CATEGORIES:
        raise HTTPException(status_code=400, detail="This category is in progress — check back soon")

    # 2. Retrieve database category knowledge
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (matched_cat,))
    cat_row = cursor.fetchone()
    conn.close()

    if not cat_row:
        act_name = "Indian Citizen Protection Acts"
        sla_days = 7
        rules = {}
    else:
        act_name = cat_row["act_name"]
        sla_days = cat_row["default_sla_days"]
        rules = json.loads(cat_row["rules_json"])

    loc_key = "rural" if is_rural else "urban"
    specific_rule = rules.get(loc_key, {})

    target_authority = specific_rule.get("authority", loc_info["body"])
    portal_link = specific_rule.get("portal", loc_info["portal"])
    helpline = specific_rule.get("helpline", loc_info["helpline"])
    compensation_clause = specific_rule.get("compensation_clause", "")

    # Build context-aware steps and DOs/DONTs
    if matched_cat == "potholes_roads":
        title = "Road Repair & Pothole Hazard Redressal"
        summary = f"Under the {act_name}, road authorities are legally mandated to keep public roads motorable and safe."
        steps = [
            {
                "step": 1,
                "title": "Document & Geo-Tag Proof",
                "detail": "Take 3 clear photos/videos of the pothole showing nearby landmarks and depth. Note exact location/cross-street."
            },
            {
                "step": 2,
                "title": f"Submit Formal Grievance to {target_authority}",
                "detail": f"File complaint on {portal_link} or call Helpline {helpline}. Demand reference ticket number."
            },
            {
                "step": 3,
                "title": f"Escalate if Unresolved after {sla_days} Days",
                "detail": f"If no action within {sla_days} days under State Right to Services Act, file Section 6(1) RTI to inspect road repair tenders."
            }
        ]
        dos = [
            "DO take photos with timestamp and GPS coordinates enabled.",
            "DO quote previous accident occurrences or risk to senior citizens/riders.",
            "DO keep medical bills or repair receipts if you suffered injury or vehicle damage."
        ]
        donts = [
            "DON'T attempt unofficial temporary repairs that alter public property without notice.",
            "DON'T close the complaint ticket until physical verification of asphalt repair is completed.",
            "DON'T pay any bribe or informal charges to municipal road workers."
        ]

    elif matched_cat == "garbage_sanitation":
        title = "Garbage Collection & Public Hygiene Entitlement"
        summary = f"Under Solid Waste Management Rules 2016, local authorities must ensure door-to-door collection and clean public spaces."
        steps = [
            {
                "step": 1,
                "title": "Photograph Waste Accumulation",
                "detail": "Capture images of uncollected garbage or open sewage causing health hazard."
            },
            {
                "step": 2,
                "title": f"Lodge Complaint with {target_authority}",
                "detail": f"Submit ticket via {portal_link} or call {helpline} (Swachh Bharat Toll-Free)."
            },
            {
                "step": 3,
                "title": "Escalate to Health Officer / BDO",
                "detail": f"If unresolved within {sla_days} days, submit written petition to Ward Sanitary Inspector / BDO."
            }
        ]
        dos = [
            "DO request neighbors to join in co-signing a joint civic petition for higher impact.",
            "DO mention public health threat (mosquito breeding, disease hazard)."
        ]
        donts = [
            "DON'T burn garbage in open public areas (violates NGT environmental norms).",
            "DON'T dump waste in unauthorized storm drains."
        ]

    elif matched_cat == "water_supply":
        title = "Clean Water Supply & Pipeline Leakage Rights"
        summary = "Right to safe, unadulterated drinking water is protected as a basic fundamental right under Article 21 of the Indian Constitution."
        steps = [
            {
                "step": 1,
                "title": "Collect Water Sample & Photo Proof",
                "detail": "Fill a clear glass bottle with contaminated tap water and take a clear video showing source."
            },
            {
                "step": 2,
                "title": f"Report Urgent Defect to {target_authority}",
                "detail": f"Register emergency ticket at {portal_link} or emergency helpline {helpline}."
            },
            {
                "step": 3,
                "title": "Demand Water Quality Test & Pipeline Inspection",
                "detail": f"Mandated SLA response time is {sla_days} days under Public Health guidelines."
            }
        ]
        dos = [
            "DO demand official water purity test report from the municipal water testing laboratory.",
            "DO keep receipts if you had to purchase private water tankers due to municipal supply failure."
        ]
        donts = [
            "DON'T consume murky or foul-smelling tap water without boiling/purification.",
            "DON'T tamper with main water distribution supply pipelines yourself."
        ]

    elif matched_cat == "consumer_rights":
        title = "Consumer Protection & Deficiency of Service"
        summary = "Under Consumer Protection Act 2019, citizens are entitled to full refund, replacement, and monetary compensation for defective goods or unfair trade practices."
        steps = [
            {
                "step": 1,
                "title": "Issue 15-Day Written Legal Notice",
                "detail": "Send formal notice to seller/manufacturer giving them 15 days to refund/replace or face court action."
            },
            {
                "step": 2,
                "title": "Lodge Grievance at National Consumer Helpline (NCH)",
                "detail": f"Register at {portal_link} or call {helpline} (1915). Most companies settle at NCH stage."
            },
            {
                "step": 3,
                "title": "File E-Daakhil Complaint at District Consumer Commission",
                "detail": f"If unresolved after 15 days, file zero-fee online claim at E-Daakhil. Claim refund + compensation for harassment."
            }
        ]
        dos = [
            "DO preserve tax invoice, order confirmation, chat transcripts, and payment receipts.",
            "DO record unboxing videos for high-value e-commerce orders."
        ]
        donts = [
            "DON'T delay filing beyond 2 years from date of cause of action (limitation period under CPA 2019).",
            "DON'T return original physical receipts—send copies and preserve originals."
        ]

    elif matched_cat == "tenant_rights":
        title = "Tenant Protection & Deposit Recovery Rights"
        summary = "Under Model Tenancy Act 2021 & Rent Control Laws, landlords cannot arbitrarily withhold security deposits, disconnect utilities, or unlawfully evict."
        steps = [
            {
                "step": 1,
                "title": "Review Registered Lease Agreement & Move-Out Proof",
                "detail": "Ensure you gave proper written notice per agreement and have video of vacant flat condition."
            },
            {
                "step": 2,
                "title": "Send Formal Demand Notice for Security Deposit Return",
                "detail": "Issue 30-day formal legal notice demanding deposit refund per Section 21 timeline (interest claims for delay depend on individual lease agreement terms)."
            },
            {
                "step": 3,
                "title": f"Petition {target_authority}",
                "detail": f"File petition before Rent Authority / Civil Court or approach Legal Aid ({helpline})."
            }
        ]
        dos = [
            "DO communicate via written email/WhatsApp messages to build legal paper trail.",
            "DO take full walkthrough video of property on the day of handing over keys."
        ]
        donts = [
            "DON'T vacate flat without receiving written acknowledgement of key handover.",
            "DON'T accept verbal promises for deposit refund after move-out."
        ]

    else: # rti_access
        title = "Right to Information (RTI) File Inspection"
        summary = "RTI Act 2005 empowers any citizen to inspect public records, road work tenders, attendance registers, and official sanction files."
        steps = [
            {
                "step": 1,
                "title": "Draft Section 6(1) RTI Questions",
                "detail": "Formulate 3-4 specific, factual questions regarding project budget, sanction officer, and delay reason."
            },
            {
                "step": 2,
                "title": f"Submit Application to PIO at {target_authority}",
                "detail": f"File online via {portal_link} or submit physical letter with Rs 10 IPO/Stamp (Free for BPL)."
            },
            {
                "step": 3,
                "title": "First Appeal if Information Refused / Delayed 30 Days",
                "detail": "If PIO does not reply in 30 days, file First Appeal under Sec 19(1). PIO faces Rs 250/day penalty under Sec 20."
            }
        ]
        dos = [
            "DO ask for certified copies of documents and site inspection records.",
            "DO keep proof of postal delivery (Registered Post AD receipt)."
        ]
        donts = [
            "DON'T ask for opinions or 'why' questions—ask for records, file notes, and copies.",
            "DON'T exceed 500 words per RTI application."
        ]

    practical_info = {
        "authority_name": target_authority,
        "portal_url": portal_link,
        "helpline": helpline,
        "compensation_clause": compensation_clause,
        "act_name": act_name,
        "default_sla_days": sla_days,
        "steps": steps,
        "dos": dos,
        "donts": donts
    }

    # Generate grounded response using Groq
    try:
        answer = generate_grounded_response(query, chunks, practical_info)
        # Append formal citations at the end of the answer
        citations_list = []
        for c in chunks:
            sec = f" Sec {c['section']}" if c.get('section') else ""
            citations_list.append(f"{c['act_name']}{sec}")
        unique_citations = sorted(list(set(citations_list)))
        citation_text = "\n\nStatutory Citations:\n" + "\n".join([f"- {cit}" for cit in unique_citations])
        grounded_summary = answer + citation_text
    except Exception as e:
        logger.error("Groq generation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Unable to generate guidance right now. Please try again."
        )

    return {
        "query": query,
        "category_id": matched_cat,
        "category_title": title,
        "summary": grounded_summary,
        "applicable_rights": [f"Right to pursue a grievance with {target_authority}", "Right to retain evidence and request a written response"],
        "location": {
            "pincode": loc_info["pincode"],
            "state": loc_info["state"],
            "district": loc_info["district"],
            "taluka": loc_info["taluka"],
            "type": loc_info["type"],
            "authority": target_authority,
            "portal": portal_link,
            "helpline": helpline
        },
        "act_name": act_name,
        "sla_days": sla_days,
        "compensation_clause": compensation_clause,
        "steps": steps,
        "dos": dos,
        "donts": donts,
        "action_buttons": [
            {"id": "draft_rti" if matched_cat == "rti_access" else ("draft_notice" if matched_cat in ["tenant_rights", "consumer_rights"] else "draft_notice"), 
             "label": "Generate RTI Application (Sec 6)" if matched_cat == "rti_access" else "Generate Legal/Grievance Notice", 
             "icon": "FileText" if matched_cat == "rti_access" else "Mail"},
            {"id": "open_portal", "label": f"Visit Grievance Portal", "url": "https://pgportal.gov.in/", "icon": "ExternalLink"}
        ]
    }
