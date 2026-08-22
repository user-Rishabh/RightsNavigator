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

    # Insert or update categories
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
            30,
            json.dumps({
                "urban": {
                    "authority": "Rent Authority / Rent Tribunal / Civil Court",
                    "portal": "State Tenancy Portal / District Collectorate",
                    "helpline": "Legal Aid Helpline 15100",
                    "compensation_clause": "Landlord cannot cut off essential water/power supply during a deposit dispute (Section 21). The Act does not fix a specific penalty rate for delayed refund - any interest owed depends on the individual lease agreement."
                },
                "rural": {
                    "authority": "Tehsildar / Revenue Inspector / District Legal Services Authority (DLSA)",
                    "portal": "NALSA Legal Aid Portal",
                    "helpline": "15100 (Free Legal Aid)",
                    "compensation_clause": "Landlord cannot cut off essential water/power supply during a deposit dispute (Section 21). The Act does not fix a specific penalty rate for delayed refund - any interest owed depends on the individual lease agreement."
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
        ),
        (
            "electricity_power",
            "Electricity & Power Supply",
            "Zap",
            "Unannounced load shedding, faulty meters, high bill disputes, delayed connection, transformer failures",
            "Electricity Act, 2003 / Electricity (Rights of Consumers) Rules 2020",
            1,
            json.dumps({
                "urban": {
                    "authority": "Electricity DISCOM Divisional Office / Consumer Grievance Redressal Forum (CGRF)",
                    "portal": "State DISCOM Consumer Portal / CPGRAMS",
                    "helpline": "1912 (Power Supply Emergency Helpline)",
                    "compensation_clause": "Under Consumer Rules 2020, DISCOM must compensate consumers for outages exceeding regulatory caps."
                },
                "rural": {
                    "authority": "Sub-Divisional Electrical Office / Gram Panchayat Electrical Assistant",
                    "portal": "Gramin Urja Portal / DISCOM Rural Cell",
                    "helpline": "1912",
                    "compensation_clause": "Transformer repair mandatory within 48 hours in rural areas under SERC standards."
                }
            })
        ),
        (
            "healthcare_patient",
            "Healthcare & Patient Rights",
            "HeartPulse",
            "Refusal of emergency treatment, hospital overcharging, medical negligence, non-availability of PHC doctors",
            "Clinical Establishments Act, 2010 / Charter of Patients' Rights (NHRC)",
            1,
            json.dumps({
                "urban": {
                    "authority": "Chief Medical Officer (CMO) / District Medical Council / Consumer Forum",
                    "portal": "State Health Dept Portal / National Consumer Helpline",
                    "helpline": "104 (Health Information Helpline) / 108 (Emergency)",
                    "compensation_clause": "Hospitals cannot deny emergency stabilization treatment for inability to pay (Supreme Court Directive)."
                },
                "rural": {
                    "authority": "Primary Health Centre (PHC) Medical Officer / District Health Officer (DHO)",
                    "portal": "National Health Mission Portal",
                    "helpline": "104 / 108",
                    "compensation_clause": "Free essential medicines and diagnostics guaranteed under NHM guidelines."
                }
            })
        ),
        (
            "labor_workplace",
            "Workplace & Labour Rights",
            "Briefcase",
            "Unpaid wages, illegal termination, workplace harassment, non-payment of PF/Gratuity, safety violations",
            "Code on Wages, 2019 / POSH Act, 2013 / EPF Act",
            15,
            json.dumps({
                "urban": {
                    "authority": "Regional Labour Commissioner / District POSH Local Committee / EPFO Tribunal",
                    "portal": "Shram Suvidha Portal / EPFiGMS (EPFO Grievance)",
                    "helpline": "1800-118-005 (EPFO Toll-Free)",
                    "compensation_clause": "Wages must be paid by 7th of every month. Delayed PF deposit incurs compound interest penalty."
                },
                "rural": {
                    "authority": "Block Development Officer (BDO - MGNREGA) / District Labour Inspector",
                    "portal": "NREGA Grievance Portal / Shram Suvidha",
                    "helpline": "1800-180-6127",
                    "compensation_clause": "Unpaid MGNREGA wages after 15 days attract 0.05% per day unemployment allowance compensation."
                }
            })
        ),
        (
            "education_rte",
            "Right to Education (RTE)",
            "GraduationCap",
            "Denial of 25% free seat quota, illegal capitation fees, denial of TC/Mark sheets, lack of school infrastructure",
            "Right of Children to Free and Compulsory Education (RTE) Act, 2009",
            7,
            json.dumps({
                "urban": {
                    "authority": "Block Education Officer (BEO) / State Commission for Protection of Child Rights (SCPCR)",
                    "portal": "State RTE Admission Portal / CPGRAMS",
                    "helpline": "1098 (Childline Helpline)",
                    "compensation_clause": "Capitation fee is strictly illegal with fine up to 10x the charged amount under RTE Sec 13."
                },
                "rural": {
                    "authority": "School Management Committee (SMC) / Block Education Officer (BEO)",
                    "portal": "Samagra Shiksha Abhiyan Portal",
                    "helpline": "1098",
                    "compensation_clause": "No child can be denied admission or held back due to lack of documents or fee shortfall."
                }
            })
        ),
        (
            "cyber_telecom",
            "Cyber Fraud & Telecom Services",
            "ShieldAlert",
            "Online banking scam, UPI fraud, SIM swap, spam calls, call drops, unauthorized VAS deductions",
            "Information Technology Act, 2000 / TRAI Telecom Consumers Protection Regulations",
            1,
            json.dumps({
                "urban": {
                    "authority": "National Cyber Crime Reporting Cell / Telecom Ombudsman / TRAI",
                    "portal": "cybercrime.gov.in / National Cyber Crime Helpline",
                    "helpline": "1930 (National Cyber Fraud Helpline)",
                    "compensation_clause": "Zero liability for unauthorized electronic banking fraud if reported within 3 days (RBI Circular)."
                },
                "rural": {
                    "authority": "Local Police Station Cyber Cell / Common Service Centre (CSC) Digital Facilitator",
                    "portal": "cybercrime.gov.in",
                    "helpline": "1930",
                    "compensation_clause": "Telecom providers must refund unauthorized value-added service deductions within 48 hours."
                }
            })
        ),
        (
            "women_elder_rights",
            "Women & Senior Citizens Rights",
            "HeartHandshake",
            "Domestic violence, maintenance claims from children, public safety, elder abuse, pension delays",
            "Protection of Women from Domestic Violence Act 2005 / Maintenance & Welfare of Parents Act 2007",
            3,
            json.dumps({
                "urban": {
                    "authority": "Protection Officer / District Social Welfare Officer / Maintenance Tribunal",
                    "portal": "National Commission for Women Portal / NALSA",
                    "helpline": "181 (Women Helpline) / 14567 (Elderline Toll-Free)",
                    "compensation_clause": "Senior Citizens Maintenance Tribunal can order children/relatives to pay up to Rs. 10,000/month."
                },
                "rural": {
                    "authority": "Gram Panchayat Nari Adalat / District Social Welfare Officer / Legal Aid Clinic",
                    "portal": "NALSA Free Legal Services Portal",
                    "helpline": "181 / 14567",
                    "compensation_clause": "Protection Orders under DV Act are enforceable immediately by local police station officer."
                }
            })
        ),
        (
            "real_estate_rera",
            "Builder & Property Disputes (RERA)",
            "Building2",
            "Builder delay in possession, unapproved layout changes, non-refund of booking advance, quality defects",
            "Real Estate (Regulation and Development) Act (RERA), 2016",
            30,
            json.dumps({
                "urban": {
                    "authority": "State Real Estate Regulatory Authority (RERA) Adjudicating Officer",
                    "portal": "State RERA Web Portal (e.g. Maharera / K-RERA / UP-RERA)",
                    "helpline": "State RERA Helpline",
                    "compensation_clause": "Builder must pay interest at SBI MCLR + 2% for every month of delayed possession."
                },
                "rural": {
                    "authority": "District Collectorate Revenue Court / District Registrar Office",
                    "portal": "State Land Records / Revenue Court Portal",
                    "helpline": "District Revenue Helpline",
                    "compensation_clause": "Sale agreements must align with standard RERA guidelines to prevent arbitrary penalty clauses."
                }
            })
        )
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO categories (id, name, icon, description, act_name, default_sla_days, rules_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
