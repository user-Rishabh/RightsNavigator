import httpx
import logging

logger = logging.getLogger("pincode_service")

# Comprehensive database of PIN code patterns & representative data for offline fast lookup
PINCODE_KNOWLEDGE = {
    # Urban Metro Examples
    "560001": {"state": "Karnataka", "district": "Bengaluru Urban", "taluka": "Bengaluru North", "type": "Urban", "body": "Bruhat Bengaluru Mahanagara Palike (BBMP)", "ward": "Shivajinagar / Central Ward", "portal": "BBMP Sahaya Portal / CPGRAMS", "helpline": "080-22660000 / 1533"},
    "110001": {"state": "Delhi", "district": "New Delhi", "taluka": "Connaught Place", "type": "Urban", "body": "New Delhi Municipal Council (NDMC)", "ward": "Zone 1", "portal": "NDMC 311 App / CPGRAMS", "helpline": "1533 / 011-23365358"},
    "400001": {"state": "Maharashtra", "district": "Mumbai City", "taluka": "Fort / South Mumbai", "type": "Urban", "body": "Brihanmumbai Municipal Corporation (BMC)", "ward": "A-Ward Fort", "portal": "MyBMC 24x7 / CPGRAMS", "helpline": "1916 / 022-22694725"},
    "600001": {"state": "Tamil Nadu", "district": "Chennai", "taluka": "George Town", "type": "Urban", "body": "Greater Chennai Corporation (GCC)", "ward": "Zone 5 (Royapuram)", "portal": "GCC Smart Chennai App / CPGRAMS", "helpline": "1913"},
    "700001": {"state": "West Bengal", "district": "Kolkata", "taluka": "BBD Bagh", "type": "Urban", "body": "Kolkata Municipal Corporation (KMC)", "ward": "Borough V", "portal": "KMC WhatsApp Grievance / CPGRAMS", "helpline": "033-22861000 / 1600"},
    "500001": {"state": "Telangana", "district": "Hyderabad", "taluka": "Abids", "type": "Urban", "body": "Greater Hyderabad Municipal Corporation (GHMC)", "ward": "Charminar Zone", "portal": "MyGHMC App / CPGRAMS", "helpline": "040-21111111 / 155304"},
    "302001": {"state": "Rajasthan", "district": "Jaipur", "taluka": "Pink City", "type": "Urban", "body": "Jaipur Greater Municipal Corporation", "ward": "Heritage Zone", "portal": "Sampark Portal Rajasthan", "helpline": "181"},
    
    # Rural / Semi-Urban Examples
    "413512": {"state": "Maharashtra", "district": "Latur", "taluka": "Ausa", "type": "Rural", "body": "Ausa Gram Panchayat / Latur Zilla Parishad", "ward": "Village Gram Sabha", "portal": "Aaple Sarkar / e-GramSwaraj", "helpline": "1800-120-8040"},
    "273001": {"state": "Uttar Pradesh", "district": "Gorakhpur", "taluka": "Sadar", "type": "Semi-Urban", "body": "Gorakhpur Nagar Nigam & Sadar Block Panchayat", "ward": "Ward 12 / Sadar Block", "portal": "Jansunwai Samadhan UP (jansunwai.up.nic.in)", "helpline": "1076 (CM Helpline)"},
    "641001": {"state": "Tamil Nadu", "district": "Coimbatore", "taluka": "Coimbatore South", "type": "Urban", "body": "Coimbatore City Municipal Corporation", "ward": "Central Zone", "portal": "TN Namma Giramam / CPGRAMS", "helpline": "0422-2302323"},
    "141001": {"state": "Punjab", "district": "Ludhiana", "taluka": "Ludhiana West", "type": "Urban", "body": "Municipal Corporation Ludhiana", "ward": "Zone A", "portal": "mSeva Punjab Portal", "helpline": "1800-180-2468"}
}

# Frequently searched neighbourhoods supplement India Post's post-office search.
# They make familiar locality names useful even when they are not a post-office name.
LOCATION_ALIASES = [
    {"name": "Maitri Park", "area": "Chembur, Mumbai, Maharashtra", "pincode": "400071", "is_village": False},
    {"name": "Punewadi", "area": "Ahmednagar, Maharashtra", "pincode": "414303", "is_village": True},
    {"name": "Bandra West", "area": "Mumbai, Maharashtra", "pincode": "400050", "is_village": False},
    {"name": "Andheri East", "area": "Mumbai, Maharashtra", "pincode": "400069", "is_village": False},
    {"name": "Koramangala", "area": "Bengaluru, Karnataka", "pincode": "560034", "is_village": False},
    {"name": "Indiranagar", "area": "Bengaluru, Karnataka", "pincode": "560038", "is_village": False},
    {"name": "Connaught Place", "area": "New Delhi, Delhi", "pincode": "110001", "is_village": False},
]

async def search_locations(query: str) -> list[dict]:
    """Return map-style Indian place suggestions with a PIN code for selection."""
    search = " ".join(query.lower().split())
    if len(search) < 2:
        return []

    # Match words individually so minor spacing/typing differences still find an area.
    words = set(search.replace(",", " ").split())
    matches = [
        item for item in LOCATION_ALIASES
        if words & set(f"{item['name']} {item['area']}".lower().replace(",", " ").split())
    ]

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Nominatim searches landmarks, colleges, roads, villages and neighbourhoods,
            # rather than limiting citizens to India Post office names.
            map_response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{query.strip()}, India", "format": "jsonv2", "addressdetails": 1, "countrycodes": "in", "limit": 8},
                headers={"User-Agent": "RightsNavigator/1.0 (civic location search)"},
            )
            if map_response.status_code == 200:
                for place in map_response.json():
                    address = place.get("address", {})
                    pincode = address.get("postcode", "").split("-")[0].strip()
                    if not (pincode.isdigit() and len(pincode) == 6):
                        continue
                    name = place.get("name") or place.get("display_name", "").split(",")[0]
                    area_parts = []
                    for key in ("suburb", "city_district", "city", "town", "village", "county", "state"):
                        value = address.get(key)
                        if value and value not in area_parts and value != name:
                            area_parts.append(value)
                    item = {
                        "name": name,
                        "area": ", ".join(area_parts[:3]) or place.get("display_name", ""),
                        "pincode": pincode,
                        "is_village": bool(address.get("village") or address.get("hamlet")),
                    }
                    if not any(existing["pincode"] == item["pincode"] and existing["name"].lower() == item["name"].lower() for existing in matches):
                        matches.append(item)

            response = await client.get(f"https://api.postalpincode.in/postoffice/{query.strip()}")
            data = response.json() if response.status_code == 200 else []
            if data and data[0].get("Status") == "Success":
                for office in data[0].get("PostOffice", [])[:6]:
                    item = {
                        "name": office.get("Name", "Locality"),
                        "area": ", ".join(filter(None, [office.get("Block"), office.get("District"), office.get("State")])),
                        "pincode": office.get("Pincode", ""),
                        "is_village": "branch" in office.get("BranchType", "").lower() or "village" in office.get("Name", "").lower(),
                    }
                    if item["pincode"] and not any(existing["pincode"] == item["pincode"] and existing["name"] == item["name"] for existing in matches):
                        matches.append(item)
    except Exception as exc:
        logger.warning(f"Location search failed: {exc}")

    return matches[:10]

async def lookup_pincode(pincode: str, locality: str = "", is_village: bool = False) -> dict:
    clean_code = pincode.strip()
    
    # 1. Direct match in curated knowledge base
    if clean_code in PINCODE_KNOWLEDGE:
        info = PINCODE_KNOWLEDGE[clean_code].copy()
        info["pincode"] = clean_code
        info["source"] = "Verified Local Authorities DB"
        if locality and is_village:
            info.update({
                "type": "Rural",
                "body": f"{locality} Gram Panchayat / {info['district']} Zilla Parishad",
                "ward": f"{locality} Village Gram Sabha",
                "portal": "e-GramSwaraj Portal (egramswaraj.gov.in) & CPGRAMS",
                "helpline": "1800-180-2000 (Panchayati Raj)",
            })
        return info

    # 2. Try online Indian Postal API (api.postalpincode.in)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"https://api.postalpincode.in/pincode/{clean_code}")
            if resp.status_code == 200:
                data = resp.json()
                if data and data[0].get("Status") == "Success":
                    offices = data[0].get("PostOffice", [])
                    if offices:
                        first_office = next((office for office in offices if locality and locality.lower() in office.get("Name", "").lower()), offices[0])
                        district = first_office.get("District", "District")
                        state = first_office.get("State", "State")
                        taluka = first_office.get("Block", first_office.get("Division", "Taluka"))
                        branch_type = first_office.get("BranchType", "")
                        
                        # Determine Urban vs Rural based on office name & branch type
                        is_rural = is_village or "Branch Office" in branch_type or "BO" in branch_type or any(kw in first_office.get("Name", "").lower() for kw in ["village", "gaon", "pally", "kheda", "pur", "gram"])
                        loc_type = "Rural" if is_rural else "Urban"

                        if is_rural:
                            body = f"{locality} Gram Panchayat / {district} Zilla Parishad" if locality else f"{taluka} Gram Panchayat / {district} Zilla Parishad"
                            portal = "e-GramSwaraj Portal (egramswaraj.gov.in) & CPGRAMS"
                            helpline = "1800-180-2000 (Panchayati Raj)"
                        else:
                            body = f"{district} Municipal Corporation / Municipality"
                            portal = "State Public Grievance Portal & CPGRAMS"
                            helpline = "1916 / District Citizen Helpline"

                        return {
                            "pincode": clean_code,
                            "state": state,
                            "district": district,
                            "taluka": taluka,
                            "type": loc_type,
                            "body": body,
                            "ward": f"{locality or first_office.get('Name')} Village Gram Sabha" if is_rural else f"{first_office.get('Name')} Division",
                            "portal": portal,
                            "helpline": helpline,
                            "source": "India Post API Live Lookup"
                        }
    except Exception as e:
        logger.warning(f"Online PIN code API lookup failed: {e}")

    # 3. Smart Heuristic Fallback based on PIN code leading digit
    digit = clean_code[0] if len(clean_code) == 6 and clean_code.isdigit() else "5"
    region_map = {
        "1": ("Delhi / Haryana / Punjab", "North Region"),
        "2": ("Uttar Pradesh / Uttarakhand", "North Central Region"),
        "3": ("Rajasthan / Gujarat", "West Region"),
        "4": ("Maharashtra / Goa / MP", "West Central Region"),
        "5": ("Andhra Pradesh / Telangana / Karnataka", "South Region"),
        "6": ("Tamil Nadu / Kerala", "South Deep Region"),
        "7": ("West Bengal / Odisha / NE", "East Region"),
        "8": ("Bihar / Jharkhand", "East Central Region")
    }
    region, label = region_map.get(digit, ("India", "National Region"))

    # Heuristic for urban vs rural based on last digits
    is_rural = is_village or (int(clean_code[-2:]) > 50 if clean_code.isdigit() and len(clean_code) == 6 else False)
    loc_type = "Rural" if is_rural else "Urban"

    if loc_type == "Rural":
        body = f"{locality} Gram Panchayat / District Zilla Parishad" if locality else "Gram Panchayat & Block Development Office (BDO)"
        portal = "e-GramSwaraj & State Jan Seva Portal"
        helpline = "1800-180-2000"
    else:
        body = f"City Municipal Corporation / Urban Development Authority"
        portal = "State Citizen Grievance Portal / CPGRAMS"
        helpline = "1916"

    return {
        "pincode": clean_code,
        "state": region,
        "district": f"District Office (PIN {clean_code})",
        "taluka": f"Taluka Centre",
        "type": loc_type,
        "body": body,
        "ward": f"{locality} Village Gram Sabha" if is_village else f"Ward / Area Jurisdiction {clean_code[-3:]}",
        "portal": portal,
        "helpline": helpline,
        "source": "Smart Geographic Heuristic Engine"
    }
