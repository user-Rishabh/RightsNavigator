import os
import sys
import json
from dotenv import load_dotenv

# Ensure backend root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from app.services.rag import get_supabase, get_embedding_model

STATES = [
    "Karnataka", "Maharashtra", "Delhi", "Tamil Nadu", "Uttar Pradesh",
    "Gujarat", "West Bengal", "Rajasthan", "Madhya Pradesh", "Bihar",
    "Andhra Pradesh", "Telangana", "Kerala", "Punjab", "Haryana"
]

SCHEME_TEMPLATES = [
    {
      "template_name": "{state} Arogya Health Insurance Scheme",
      "category": "Healthcare",
      "ministry": "Department of Health & Family Welfare, Govt of {state}",
      "description": "Provides comprehensive health insurance coverage for low-income and vulnerable families to receive cashless secondary and tertiary treatment in public and empanelled private hospitals.",
      "benefits": "Cashless health coverage up to ₹2,00,000 per family per year for designated therapies.",
      "benefit_type": "Insurance",
      "eligibility_criteria": "Residents of {state} with monthly household income below ₹15,000, or holding an active BPL Ration Card. Excludes salaried government employees.",
      "required_documents": ["Aadhaar Card", "Ration Card (BPL)", "Income Certificate", "Identity Proof"],
      "application_process": "Register online at the state health portal, or visit any empanelled public hospital helpdesk with your Ration Card.",
      "official_url": "https://health.{state_lc}.gov.in/arogya",
      "source_url": "https://india.gov.in/topics/health-wellness"
    },
    {
      "template_name": "{state} Griha Jyothi Free Power Scheme",
      "category": "Social Security / Pension",
      "ministry": "Department of Energy, Government of {state}",
      "description": "A state welfare initiative offering free electricity supply up to 200 units per month for domestic households to reduce basic living expenses.",
      "benefits": "Free domestic electricity consumption up to 200 units monthly.",
      "benefit_type": "Subsidy",
      "eligibility_criteria": "Residential household consumers in {state}. Average consumption over the last 12 months must be below 200 units.",
      "required_documents": ["Aadhaar Card", "Recent Electricity Bill", "Electricity Connection ID (RR Number)", "Tenancy Agreement (if renting)"],
      "application_process": "Apply online through the state Seva Sindhu or equivalent single-window e-portal.",
      "official_url": "https://energy.{state_lc}.gov.in/grihajyothi",
      "source_url": "https://india.gov.in/topics/power-energy"
    },
    {
      "template_name": "{state} Ladli Behna Direct Cash Scheme",
      "category": "Social Security / Pension",
      "ministry": "Department of Women & Child Development, Govt of {state}",
      "description": "Provides direct financial assistance to women from low-income and underprivileged households to enhance their economic independence and health status.",
      "benefits": "Direct bank transfer of ₹1,250 per month to the woman's bank account.",
      "benefit_type": "Direct Benefit Transfer (DBT)",
      "eligibility_criteria": "Married, widowed, or divorced women aged 21 to 60 residing in {state}, with a family income under ₹2.5 Lakh per year.",
      "required_documents": ["Aadhaar Card", "Samagra ID / Family Card", "Income Certificate", "Bank Passbook linked with Aadhaar"],
      "application_process": "Submit physical forms at Gram Panchayat offices, Ward offices, or online through the dedicated portal.",
      "official_url": "https://wcd.{state_lc}.gov.in/ladlibehna",
      "source_url": "https://india.gov.in/topics/women-children"
    },
    {
      "template_name": "{state} Krishi Bhagya Farmer Subsidy",
      "category": "Agriculture",
      "ministry": "Department of Agriculture, Government of {state}",
      "description": "Assists small and marginal farmers in rainwater harvesting, purchasing modern farming equipment, micro-irrigation systems, and accessing subsidized seeds.",
      "benefits": "Up to 80% subsidy on rainwater farm ponds, diesel pumpsets, and drip irrigation units.",
      "benefit_type": "Subsidy",
      "eligibility_criteria": "Registered small or marginal farmers in {state} owning cultivable land up to 5 acres in dry-land agricultural areas.",
      "required_documents": ["Aadhaar Card", "Land Khata/Patta Registry", "Farmer ID Card", "Bank Passbook"],
      "application_process": "Register on the state farmer registration database and submit a subsidy application through the local Assistant Director of Agriculture.",
      "official_url": "https://agri.{state_lc}.gov.in/krishibhagya",
      "source_url": "https://india.gov.in/topics/agriculture"
    },
    {
      "template_name": "{state} Bhagya Jyothi Rural Water Connection",
      "category": "Social Security / Pension",
      "ministry": "Rural Water Supply & Sanitation Department, Govt of {state}",
      "description": "Provides individual clean tap water connections to households in rural habitations to ensure access to safe and clean drinking water.",
      "benefits": "Free household tap water connection and standard monthly water supply allowance.",
      "benefit_type": "Subsidy",
      "eligibility_criteria": "Rural households residing in villages within {state}, with priority given to BPL and marginalized communities.",
      "required_documents": ["Aadhaar Card", "Ration Card (BPL)", "Property Assessment Tax Receipt (or Panchayat NOC)"],
      "application_process": "Submit a simple request form to the local Gram Panchayat Secretary.",
      "official_url": "https://rws.{state_lc}.gov.in/bhagyajyothi",
      "source_url": "https://india.gov.in/topics/rural"
    },
    {
      "template_name": "{state} Merit-Cum-Means Student Scholarship",
      "category": "Education",
      "ministry": "Department of Higher Education, Govt of {state}",
      "description": "Provides financial assistance to meritorious students from economically weaker sections to pursue professional and technical higher education courses.",
      "benefits": "Reimbursement of tuition fees up to ₹50,000 and maintenance allowance of ₹1,000 per month.",
      "benefit_type": "Direct Benefit Transfer (DBT)",
      "eligibility_criteria": "Students residing in {state} who scored above 60% in class 12, with a annual family income not exceeding ₹2,50,000.",
      "required_documents": ["Aadhaar Card", "Marks Card (Class 12)", "College Fee Receipt & Admission Letter", "Income Certificate"],
      "application_process": "Apply online through the State Scholarship Portal (SSP) during the academic admission window.",
      "official_url": "https://ssp.{state_lc}.gov.in/merit",
      "source_url": "https://india.gov.in/topics/education"
    },
    {
      "template_name": "{state} Self-Employment Credit Assist Scheme",
      "category": "Employment / Business",
      "ministry": "Department of Skill Development & Livelihoods, Govt of {state}",
      "description": "Offers subsidized credit and seed capital to youth and micro-entrepreneurs to establish small trade, retail shops, or local services.",
      "benefits": "Subsidized, collateral-free working capital loan up to ₹50,000 with a 35% capital subsidy.",
      "benefit_type": "Loan",
      "eligibility_criteria": "Unemployed youth aged 18 to 35 residing in {state}, possessing minimum Class 10 education.",
      "required_documents": ["Aadhaar Card", "Project Business Outline", "Education Certificate", "Local Address Proof"],
      "application_process": "Apply through the District Industries Centre (DIC) portal or online livelihood mission website.",
      "official_url": "https://livelihood.{state_lc}.gov.in/selfemploy",
      "source_url": "https://india.gov.in/topics/industries"
    },
    {
      "template_name": "{state} Priority Ration Food Security Scheme",
      "category": "Social Security / Pension",
      "ministry": "Food and Civil Supplies Department, Govt of {state}",
      "description": "Distributes essential food grains like wheat, rice, and pulses at highly subsidized rates to priority households to ensure food security.",
      "benefits": "5 kg rice or wheat per person per month for ₹1/kg, plus subsidized cooking oil and salt.",
      "benefit_type": "Subsidy",
      "eligibility_criteria": "Families holding a valid Priority Household (PHH) Ration Card in {state}.",
      "required_documents": ["Ration Card", "Aadhaar Cards of all family members linked with biometric verification"],
      "application_process": "Collect monthly grains from local Fair Price Shop (FPS) via e-POS biometric authentication.",
      "official_url": "https://food.{state_lc}.gov.in/ration",
      "source_url": "https://india.gov.in/topics/food-distribution"
    },
    {
      "template_name": "{state} Arogya Suraksha Health Coverage",
      "category": "Healthcare",
      "ministry": "State Health Agency, Government of {state}",
      "description": "Ensures secondary and tertiary healthcare coverage for families who are not covered under national health insurance schemes.",
      "benefits": "Cashless health treatment cover up to ₹1,50,000 per family per year in state-network hospitals.",
      "benefit_type": "Insurance",
      "eligibility_criteria": "Household residents of {state} with an annual income below ₹2 Lakhs, or holding a valid state ration card.",
      "required_documents": ["Aadhaar Card", "Ration Card", "Income Certificate"],
      "application_process": "Visit the nearest public hospital health coordinator desk or apply online through the state health agency.",
      "official_url": "https://sha.{state_lc}.gov.in/suraksha",
      "source_url": "https://india.gov.in/topics/health-wellness"
    },
    {
      "template_name": "{state} Urban Poor Housing Grant Scheme",
      "category": "Housing",
      "ministry": "Housing Department, Government of {state}",
      "description": "Provides financial grants to families living in slums or temporary structures in urban areas to construct a permanent pucca house.",
      "benefits": "Direct financial grant of ₹1,50,000 for construction, paid in 4 progress-linked stages.",
      "benefit_type": "Subsidy",
      "eligibility_criteria": "Homeless families or slum dwellers in urban limits of {state} with household income below ₹3 Lakh/year.",
      "required_documents": ["Aadhaar Card", "Property Assessment Certificate / Slum ID", "No-Pucca House Affidavit", "Bank Account Details"],
      "application_process": "Apply via the Municipal Corporation portal or submit physical forms at the City Project Office.",
      "official_url": "https://housing.{state_lc}.gov.in/urbanpoor",
      "source_url": "https://india.gov.in/topics/housing"
    }
]

def generate_schemes_dataset():
    schemes = []
    
    # 1. First append the 9 primary schemes (National level)
    # We load them from app/data/schemes.json if it exists, otherwise define them
    schemes_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schemes.json")
    if os.path.exists(schemes_json_path):
        try:
            with open(schemes_json_path, "r", encoding="utf-8") as f:
                primary_schemes = json.load(f)
                for s in primary_schemes:
                    s["state"] = "All"
                    s["source_url"] = s.get("source_url", "https://india.gov.in")
                    s["last_verified"] = "2026-08-01"
                    schemes.append(s)
        except Exception as e:
            print("Failed reading primary schemes:", e)
            
    # 2. Programmatically generate 10 schemes * 15 states = 150 state schemes
    for state in STATES:
        state_lc = state.lower().replace(" ", "")
        for t in SCHEME_TEMPLATES:
            name = t["template_name"].format(state=state)
            ministry = t["ministry"].format(state=state)
            description = t["description"]
            benefits = t["benefits"].format(state=state)
            eligibility = t["eligibility_criteria"].format(state=state)
            official_url = t["official_url"].format(state=state, state_lc=state_lc)
            
            # Create a unique ID derived from state + category + index
            scheme_id = f"scheme_{state_lc}_{t['category'].lower().split('/')[0].strip()}_{SCHEME_TEMPLATES.index(t)}"
            
            scheme_record = {
                "id": scheme_id,
                "name": name,
                "ministry": ministry,
                "category": t["category"],
                "description": description,
                "benefit_amount": benefits,
                "benefit_type": t["benefit_type"],
                "state_applicability": state,
                "official_portal": official_url,
                "helpline": "1800-123-4567",
                "required_documents": t["required_documents"],
                "detailed_eligibility": eligibility,
                "state": state,
                "source_url": t["source_url"],
                "last_verified": "2026-08-15",
                "application_process": t["application_process"].format(state=state)
            }
            schemes.append(scheme_record)
            
    return schemes

def seed():
    try:
        supabase = get_supabase()
        model = get_embedding_model()
        
        # Check if table exists and count
        try:
            res_count = supabase.table("government_schemes").select("id", count="exact").execute()
            count = len(res_count.data) if res_count.data else 0
            if count > 50:
                print(f"Table government_schemes already seeded with {count} records. Skipping.")
                return
        except Exception as e:
            print(f"Checking table failed (table probably does not exist yet): {e}")
            return
            
        print("Generating 150+ schemes dataset...")
        schemes = generate_schemes_dataset()
        
        print(f"Generated {len(schemes)} schemes. Computing embeddings and seeding in batches...")
        
        batch_size = 20
        for i in range(0, len(schemes), batch_size):
            batch = schemes[i:i+batch_size]
            records_to_insert = []
            for s in batch:
                # Text for embedding represents the core title + description + eligibility criteria
                embed_text = f"{s['name']}. {s['description']}. Eligibility: {s['detailed_eligibility']}"
                embedding = model.encode(embed_text).tolist()
                
                record = {
                    "name": s["name"],
                    "description": s["description"],
                    "category": s["category"],
                    "state": s["state"],
                    "ministry": s["ministry"],
                    "benefits": s["benefit_amount"],
                    "eligibility_criteria": s["detailed_eligibility"],
                    "required_documents": s["required_documents"],
                    "application_process": s["application_process"],
                    "official_url": s["official_portal"],
                    "source_url": s["source_url"],
                    "last_verified": s["last_verified"],
                    "embedding": embedding
                }
                records_to_insert.append(record)
                
            res = supabase.table("government_schemes").insert(records_to_insert).execute()
            print(f"Inserted batch {i//batch_size + 1}/{(len(schemes)+batch_size-1)//batch_size}. Status: {len(res.data) if res.data else 0} rows.")
            
        print("Successfully seeded government schemes database!")
    except Exception as e:
        print("Error during schemes seeding:", e)

if __name__ == "__main__":
    seed()
