from datetime import datetime
import os
import httpx


async def generate_ai_draft(doc_type: str, fallback: str, details: str, authority_name: str) -> tuple[str, str]:
    """Use Gemini when configured; retain a dependable local legal template offline."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback, "template"

    prompt = f"""You are RightsNavigator, a careful Indian civic-rights drafting assistant.
Rewrite the draft below for the user's facts. Document type: {doc_type}. Authority/opponent: {authority_name}.
Facts supplied by the citizen: {details}

Rules: retain only accurate statutory references already present in the draft; do not invent facts, dates, amounts, case law, or legal outcomes; use clear formal Indian-English; preserve placeholders where facts are missing; add a short 'Before sending' checklist at the end; include 'This is an informational draft, not legal advice.'

DRAFT:\n{fallback}"""
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(url, params={"key": api_key}, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.25, "maxOutputTokens": 2200},
            })
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text or fallback, "gemini"
    except Exception:
        return fallback, "template"

def generate_rti_application(citizen_name: str, address: str, pincode: str, authority_name: str, subject: str, questions: list) -> str:
    today_str = datetime.now().strftime("%B %d, %Y")
    q_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    return f"""FORM 'A' - APPLICATION FOR OBTAINING INFORMATION UNDER THE RIGHT TO INFORMATION ACT, 2005
[Section 6(1) of RTI Act 2005]

Date: {today_str}

To,
The Public Information Officer (PIO) / Assistant PIO
Office of {authority_name}
PIN Code / Jurisdiction: {pincode}

1. Name of the Applicant : {citizen_name or '[Citizen Full Name]'}
2. Address for Communication : {address or '[Complete Postal Address]'}, PIN: {pincode}
3. Particulars of Information Required:
   Subject: {subject or 'Inspection of public works, tender allocations, and grievance delay records'}

4. Specific Questions / Information sought:
{q_text if questions else '''1. Provide certified copies of work orders and tenders sanctioned for the subject location in the last 12 months.
2. Provide daily progress report, measurement book entries, and names of contractor/engineers accountable.
3. Provide certified copy of action taken on citizens' previous complaints filed for this issue.
4. State the exact reason for delay and expected date of completion as per Right to Service Act norms.'''}

5. Period to which information relates : Last 2 Years to Present
6. Application Fee Details : Rs. 10/- attached herewith via Court Fee Stamp / Postal Order / Online Payment.
   (Note: BPL applicant exempt as per Sec 7(5) of RTI Act 2005).

7. Format of Information Required : Certified copies by Speed Post / Email.

I state that the information sought does not fall under any exemptions specified under Section 8 or 9 of the Right to Information Act 2005.

Yours faithfully,

_______________________
(Signature of Applicant)
Name: {citizen_name or '[Citizen Full Name]'}
Mobile: [Citizen Mobile Number]
Email: [Citizen Email Address]
"""

def generate_legal_notice(doc_type: str, citizen_name: str, address: str, opponent_name: str, details: str, pincode: str, authority_name: str) -> str:
    today_str = datetime.now().strftime("%B %d, %Y")

    if doc_type == "consumer_notice":
        return f"""REGISTERED POST WITH ACKNOWLEDGEMENT DUE / LEGAL NOTICE
UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019

Date: {today_str}

To,
The Managing Director / Authorized Representative
{opponent_name or '[Company / Seller / Service Provider Name]'}
Address: [Opponent Address]

Subject: LEGAL NOTICE FOR DEFICIENCY OF SERVICE / UNFAIR TRADE PRACTICE REGARDING ORDER/PRODUCT.

Sir/Madam,

Under instructions from my client/on my own behalf, {citizen_name or '[Citizen Name]'}, residing at {address or '[Citizen Address]'}, PIN {pincode}, I hereby serve you with this Legal Notice:

1. That on or about [Date], I purchased/availed services regarding:
   "{details or 'Defective goods/service provided without resolution despite repeated requests.'}"

2. That the product/service supplied by your organization suffered from severe deficiency, breach of warranty, and unfair trade practice under Section 2(47) of the Consumer Protection Act, 2019.

3. That despite multiple oral and written communications, you failed and neglected to rectify the deficiency or refund the amount of Rs. [Amount], causing immense mental agony, financial loss, and frustration.

TAKE NOTICE that you are hereby called upon to:
a) Refund the full amount of Rs. [Amount] paid towards the purchase/service together with 18% p.a. interest;
b) Pay a sum of Rs. 25,000/- towards compensation for mental torture and litigation expenses;
within FIFTEEN (15) DAYS from the receipt of this notice, failing which appropriate legal proceedings shall be instituted against you before the District Consumer Disputes Redressal Commission at your cost and risk.

Yours faithfully,

_______________________
{citizen_name or '[Citizen Full Name]'}
Contact: [Phone / Email]
Address: {address or '[Address]'}, PIN: {pincode}
"""

    elif doc_type == "tenant_notice":
        return f"""FORMAL LEGAL DEMAND NOTICE FOR RETURN OF SECURITY DEPOSIT
UNDER THE MODEL TENANCY ACT / RENT CONTROL PROVISIONS

Date: {today_str}

To,
{opponent_name or '[Landlord / Property Owner Name]'}
Address: [Landlord Address]

Subject: DEMAND FOR IMMEDIATE REFUND OF SECURITY DEPOSIT FOR PREMISES AT [Property Address].

Dear {opponent_name or 'Landlord'},

I was the legal tenant in respect of your premises situated at [Property Address], which was peacefully vacated and handed over on [Date of Move Out] after giving due written notice.

1. That at the time of commencement of tenancy, I paid a refundable Security Deposit of Rs. [Deposit Amount] via [Bank Transfer/Cheque].
2. That all utility bills (electricity, water, maintenance) have been fully paid up to date and no damage was caused to the premises.
3. That as per Model Tenancy guidelines and standard lease terms, the security deposit must be refunded within 30 days of handing over vacant possession.
4. That despite 30 days having elapsed, you have unlawfully withheld the security deposit of Rs. [Deposit Amount] without valid legal justification.

THEREFORE, YOU ARE HEREBY CALLED UPON to refund the full security deposit amount of Rs. [Deposit Amount] along with 18% p.a. interest from the date of handover to my bank account within SEVEN (7) DAYS of receipt of this notice.

Failure to do so will constrain me to file a petition before the Rent Authority / Rent Tribunal and District Legal Services Authority seeking recovery, damages, and full legal costs.

Yours sincerely,

_______________________
{citizen_name or '[Tenant Name]'}
Phone: [Mobile Number]
Email: [Email Address]
"""

    else: # municipal / road / sanitation grievance letter
        return f"""FORMAL CIVIC COMPLAINT & NOTICE OF STATUTORY DUTY
[Under State Right to Public Services Act & Municipal Corporation Act]

Date: {today_str}

To,
The Executive Engineer / Chief Officer / Ward Commissioner
{authority_name or 'Municipal Corporation / Gram Panchayat Office'}
Jurisdiction PIN Code: {pincode}

Subject: URGENT COMPLAINT REGARDING CIVIC DEFECT AT LOCATION: {address or '[Location / Street Address]'}.

Sir/Madam,

I am a resident/taxpayer residing at {address or '[Address]'}, PIN {pincode}. I bring to your urgent attention a severe civic hazard/neglect:

DETAILS OF GRIEVANCE:
"{details or 'Hazardous un-repaired pothole / uncollected garbage / water supply contamination posing immediate risk to citizens.'}"

STATUTORY OBLIGATION:
Under the Municipal Corporation Act and State Right to Public Services Act, your office is legally bound to maintain safe public thoroughfares, sanitation, and hygiene. Under Section 198A of the Motor Vehicles Act 1988 (Amended 2019), road maintenance authorities face strict penalties for failing to maintain safe road design and repair.

REQUEST FOR IMMEDIATE ACTION:
1. Conduct an immediate spot inspection of the affected area within 24 hours.
2. Initiate repair/remediation works within {7 if doc_type=='road' else 3} days.
3. Provide written confirmation and grievance reference number for tracking.

If this hazard remains unaddressed within the statutory period, I shall be forced to escalate this matter to the District Collector, file a Section 6(1) RTI application for tender inspection, and approach the State Human Rights Commission / Consumer Forum for public negligence compensation.

Thanking you,

Yours faithfully,

_______________________
Name: {citizen_name or '[Citizen Name]'}
Address: {address or '[Address]'}, PIN: {pincode}
Contact: [Mobile Number]
"""
