import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rights_navigator.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Cases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            pincode TEXT NOT NULL,
            location_type TEXT NOT NULL,
            authority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details_json TEXT
        )
    ''')

    # Knowledge / Category table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT NOT NULL,
            act_name TEXT NOT NULL,
            default_sla_days INTEGER NOT NULL,
            rules_json TEXT NOT NULL
        )
    ''')

    # Insert initial categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        categories_data = [
            (
                "potholes_roads",
                "Potholes & Road Repairs",
                "Construction",
                "Damaged roads, hazardous potholes, unfinished roadwork, traffic signal failures",
                "State Right to Public Services Act / Motor Vehicles Act Sec 198A",
                7,
                json.dumps({
                    "urban": {
                        "authority": "Municipal Corporation (PWD / Executive Engineer Roads)",
                        "portal": "CPGRAMS / Local Municipal Smart City App",
                        "helpline": "1916 / Municipal Toll-Free",
                        "compensation_clause": "Under MV Act 198A, road design & maintenance authorities face penalties up to Rs. 1 Lakh for non-compliance."
                    },
                    "rural": {
                        "authority": "Gram Panchayat Secretary / Zilla Parishad PWD Overseer",
                        "portal": "e-GramSwaraj / CPGRAMS",
                        "helpline": "1800-180-2000 (Panchayati Raj Helpline)",
                        "compensation_clause": "PMGSY / State Rural Road Development Agency monitoring division."
                    }
                })
            ),
            (
                "garbage_sanitation",
                "Garbage & Public Sanitation",
                "Trash2",
                "Uncollected garbage, overflowing public dumpsters, open sewage, lack of public toilets",
                "Swachh Bharat Abhiyan Guidelines / Municipal Solid Waste Rules 2016",
                3,
                json.dumps({
                    "urban": {
                        "authority": "Municipal Ward Sanitary Inspector / Chief Health Officer",
                        "portal": "Swachhata App (MoHUA) / CPGRAMS",
                        "helpline": "1969 (Swachh Bharat Toll-Free)",
                        "compensation_clause": "Failure to collect waste within 48h violates MSW Management Rules 2016."
                    },
                    "rural": {
                        "authority": "Gram Panchayat Swachhata Samiti / Block Development Officer (BDO)",
                        "portal": "Swachh Bharat Mission Gramin Portal",
                        "helpline": "1800-111-555",
                        "compensation_clause": "Gram Panchayat Swachhata fund mandate under 15th Finance Commission."
                    }
                })
            ),
            (
                "water_supply",
                "Water Supply & Contamination",
                "Droplets",
                "No water supply, contaminated tap water, pipeline leaks, drainage overflow",
                "Jal Jeevan Mission / State Water Supply & Sewerage Act",
                2,
                json.dumps({
                    "urban": {
                        "authority": "City Water Supply & Sewerage Board (BWSSB / DJB / DJB Ward Office)",
                        "portal": "State Water Board Portal / CPGRAMS",
                        "helpline": "1916 / Water Board Helpline",
                        "compensation_clause": "Safe drinking water is a fundamental right under Article 21 (Attakoya Thangal v. Union of India)."
                    },
                    "rural": {
                        "authority": "Village Water & Sanitation Committee (VWSC) / PHED Assistant Engineer",
                        "portal": "Jal Jeevan Mission Citizen Dashboard",
                        "helpline": "1800-180-1551",
                        "compensation_clause": "Har Ghar Jal quality testing directive under PHED guidelines."
                    }
                })
            ),
            (
                "consumer_rights",
                "Consumer Protection & Refunds",
                "ShoppingBag",
                "Defective products, refusal of refund, false advertising, overpriced billing, e-commerce fraud",
                "Consumer Protection Act, 2019",
                15,
                json.dumps({
                    "urban": {
                        "authority": "District Consumer Disputes Redressal Commission (DCDRC) / National Consumer Helpline",
                        "portal": "National Consumer Helpline (NCH) / E-Daakhil Portal",
                        "helpline": "1915 or SMS 8800001915",
                        "compensation_clause": "Right to 100% refund plus compensation for mental agony and litigation costs under CPA 2019."
                    },
                    "rural": {
                        "authority": "District Consumer Commission / Common Service Centre (CSC) Facilitator",
                        "portal": "E-Daakhil Portal (via CSC VLE)",
                        "helpline": "1915",
                        "compensation_clause": "Claims up to Rs. 50 Lakhs can be filed at District Commission with zero fee up to Rs. 5 Lakhs."
                    }
                })
            ),
            (
                "tenant_rights",
                "Tenant Rights & Rent Disputes",
                "Home",
                "Unlawful eviction notice, security deposit withholding, refusal of urgent repairs, utility cutoff",
                "Model Tenancy Act, 2021 / State Rent Control Act",
                14,
                json.dumps({
                    "urban": {
                        "authority": "Rent Authority / Rent Tribunal / Civil Court",
                        "portal": "State Tenancy Portal / District Collectorate",
                        "helpline": "Legal Aid Helpline 15100",
                        "compensation_clause": "Landlord cannot cut off essential water/power supply. Unlawful retention of deposit incurs interest penalty."
                    },
                    "rural": {
                        "authority": "Tehsildar / Revenue Inspector / District Legal Services Authority (DLSA)",
                        "portal": "NALSA Legal Aid Portal",
                        "helpline": "15100 (Free Legal Aid)",
                        "compensation_clause": "Model Tenancy Act mandates refund of security deposit within 1 month of vacating."
                    }
                })
            ),
            (
                "rti_access",
                "RTI (Right to Information)",
                "FileText",
                "Seeking government inspection of works, tender details, fund allocation, delay reason in files",
                "Right to Information Act, 2005",
                30,
                json.dumps({
                    "urban": {
                        "authority": "Public Information Officer (PIO), Municipal Corp / State Govt Dept",
                        "portal": "RTI Online Portal (rtionline.gov.in / State RTI Portal)",
                        "helpline": "State Information Commission Helpline",
                        "compensation_clause": "PIO faces penalty of Rs. 250/day up to Rs. 25,000 for delayed/refused information under Sec 20(1)."
                    },
                    "rural": {
                        "authority": "Public Information Officer (PIO), Block Development Office / Panchayat Secretary",
                        "portal": "Physical Application to PIO / State RTI Portal",
                        "helpline": "15100 / State Information Commission",
                        "compensation_clause": "BPL card holders are completely exempt from Rs 10 RTI application fee."
                    }
                })
            )
        ]
        cursor.executemany(
            "INSERT INTO categories (id, name, icon, description, act_name, default_sla_days, rules_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            categories_data
        )

    # Insert sample seed cases
    cursor.execute("SELECT COUNT(*) FROM cases")
    if cursor.fetchone()[0] == 0:
        seed_cases = [
            ("CASE-2026-881", "Hazardous Pothole on Main MG Road", "potholes_roads", "560001", "Urban", "BBMP Executive Engineer (Roads)", "In Progress", json.dumps({"step": 2, "sla_days": 7, "filed_on": "2026-08-18"})),
            ("CASE-2026-904", "Security Deposit Withheld by Landlord", "tenant_rights", "110001", "Urban", "Delhi Rent Authority", "Draft Notice Sent", json.dumps({"step": 1, "sla_days": 14, "filed_on": "2026-08-19"}))
        ]
        cursor.executemany(
            "INSERT INTO cases (id, title, category, pincode, location_type, authority, status, details_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            seed_cases
        )

    conn.commit()
    conn.close()
