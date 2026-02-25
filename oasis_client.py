"""OaSIS (Occupational and Skills Information System) API client.

Performs an Advanced Interest Search on the OaSIS website to find
NOC occupations matching a user's Holland Code interest profile.
"""

import re

import requests
import streamlit as st
from bs4 import BeautifulSoup

# Holland Code interest types → OaSIS interest IDs
HOLLAND_CODES = {
    "Realistic": "C.01.a.01",
    "Investigative": "C.01.a.02",
    "Artistic": "C.01.a.03",
    "Social": "C.01.a.04",
    "Enterprising": "C.01.a.05",
    "Conventional": "C.01.a.06",
}

# Short descriptions for each Holland type
HOLLAND_DESCRIPTIONS = {
    "Realistic": "Hands-on work with tools, machines, plants, or animals",
    "Investigative": "Research, analysis, and problem-solving",
    "Artistic": "Creative expression, design, and communication",
    "Social": "Helping, teaching, counselling, and serving others",
    "Enterprising": "Leading, persuading, managing, and selling",
    "Conventional": "Organizing data, following procedures, and detail work",
}

OASIS_BASE_URL = "https://noc.esdc.gc.ca"
OASIS_FORM_URL = f"{OASIS_BASE_URL}/Oasis/OasisAdvancedSearch"
OASIS_SUBMIT_URL = f"{OASIS_BASE_URL}/OaSIS/AdvancedInterestSearchSubmit"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_oasis_matches(
    interest_1: str, interest_2: str, interest_3: str
) -> dict:
    """Query OaSIS Advanced Interest Search and return matching NOC codes.

    Args:
        interest_1: Most dominant Holland interest name (e.g. "Realistic")
        interest_2: Second most dominant
        interest_3: Third most dominant

    Returns:
        {
            "success": bool,
            "noc_codes": ["21232", "21231", ...],  # 5-digit NOC codes
            "matches": [{"code": "21232", "title": "Software developers..."}, ...],
            "error": str or None
        }
    """
    id_1 = HOLLAND_CODES.get(interest_1)
    id_2 = HOLLAND_CODES.get(interest_2)
    id_3 = HOLLAND_CODES.get(interest_3)

    if not (id_1 and id_2 and id_3):
        return {
            "success": False,
            "noc_codes": [],
            "matches": [],
            "error": "Invalid interest selections",
        }

    try:
        session = requests.Session()
        session.verify = False

        # Suppress SSL warnings for this session
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # GET the form page to extract CSRF token
        form_resp = session.get(OASIS_FORM_URL, timeout=15)
        form_resp.raise_for_status()

        soup = BeautifulSoup(form_resp.text, "html.parser")
        token_input = soup.find(
            "input", {"name": "__RequestVerificationToken"}
        )
        token = token_input["value"] if token_input else ""

        # POST the interest search form
        form_data = {
            "__RequestVerificationToken": token,
            "VeryDominanceValue": id_1,
            "DominanceValue": id_2,
            "LessDominanceValue": id_3,
            "ddlVersions": "2025.0",
            "isExactOrder": "false",
            "Item2": "",
        }

        resp = session.post(
            OASIS_SUBMIT_URL,
            data=form_data,
            timeout=20,
            headers={
                "Referer": OASIS_FORM_URL,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        resp.raise_for_status()

        # Parse the result HTML for NOC codes and titles
        result_soup = BeautifulSoup(resp.text, "html.parser")
        matches = _parse_results(result_soup)

        noc_codes = [m["code"] for m in matches]

        return {
            "success": True,
            "noc_codes": noc_codes,
            "matches": matches,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "noc_codes": [],
            "matches": [],
            "error": str(e),
        }


def _parse_results(soup: BeautifulSoup) -> list[dict]:
    """Extract 5-digit NOC codes and titles from OaSIS result HTML.

    OaSIS links use format: /OASIS/OASISOccProfile?code=XXXXX.XX&version=...
    with link text like "21232.00 – Software developers and programmers".
    We extract the 5-digit base code (ignoring the .XX suffix).
    """
    matches = []
    seen_codes = set()

    # Look for OaSIS profile links with code= parameter
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Match code=XXXXX.XX in query params
        code_match = re.search(r"code=(\d{5})(?:\.\d+)?", href)
        if code_match:
            code = code_match.group(1)
            if code not in seen_codes:
                seen_codes.add(code)
                title = link.get_text(strip=True)
                # Clean up title — remove leading "XXXXX.XX – " prefix
                title = re.sub(r"^\d{5}(?:\.\d+)?\s*[-–—]\s*", "", title)
                matches.append({"code": code, "title": title})

    # Fallback: scan all text for XXXXX.XX patterns if no links found
    if not matches:
        text = soup.get_text()
        for m in re.finditer(
            r"\b(\d{5})(?:\.\d+)?\s*[-–—]\s*(.+?)(?:\n|$)", text
        ):
            code = m.group(1)
            if code not in seen_codes:
                seen_codes.add(code)
                matches.append({
                    "code": code,
                    "title": m.group(2).strip(),
                })

    return matches


def _extract_profile_description(html: str) -> str | None:
    """Extract the occupation description from an OaSIS profile page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    if "Error 404" in soup.get_text():
        return None
    h2_list = soup.find_all("h2")
    for h2 in h2_list:
        txt = h2.get_text(strip=True)
        if txt and txt not in (
            "View occupational profile",
            "Overview",
            "Work characteristics",
        ):
            p = h2.find_next("p")
            if p:
                desc = p.get_text(strip=True)
                if desc and "Error 404" not in desc:
                    return desc
            break
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_hierarchy_page() -> str:
    """Fetch and cache the OaSIS hierarchy page HTML."""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    resp = requests.get(
        f"{OASIS_BASE_URL}/OaSIS/OaSISHierarchy",
        verify=False, timeout=20,
    )
    return resp.text if resp.status_code == 200 else ""


def _find_sub_profiles(noc_code: str, hierarchy_html: str) -> list[dict]:
    """Find sub-profiles (e.g. 40021.01, 40021.02) for a NOC code from the hierarchy page.

    Returns list of {"code": "40021.01", "title": "School principals"}.
    """
    soup = BeautifulSoup(hierarchy_html, "html.parser")
    subs = []
    seen = set()
    # Find the h3 for this code, then get sub-profile links from its next sibling
    for h3 in soup.find_all("h3"):
        if noc_code in h3.get_text():
            sibling = h3.find_next_sibling()
            if sibling:
                for a in sibling.find_all("a", href=True):
                    link_text = a.get_text(strip=True)
                    # Match "XXXXX.XX – Title" pattern
                    m = re.match(
                        r"(\d{5}\.\d{2})\s*[–—-]\s*(.+)", link_text
                    )
                    if m and m.group(1) not in seen:
                        seen.add(m.group(1))
                        subs.append({
                            "code": m.group(1),
                            "title": m.group(2).strip(),
                        })
            break
    return subs


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_noc_description(noc_code: str) -> dict:
    """Fetch the occupation description from OaSIS for a 5-digit NOC code.

    First tries the direct profile page (code.00). If that returns 404,
    looks up sub-profiles from the hierarchy page and fetches each.

    Returns:
        {
            "description": str or None,     # main description (from .00 profile)
            "sub_profiles": [               # empty if .00 exists directly
                {"code": "40021.01", "title": "School principals",
                 "description": "School principals plan..."},
                ...
            ]
        }
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    result = {"description": None, "sub_profiles": []}

    # Try the direct .00 profile first
    url = f"{OASIS_BASE_URL}/OASIS/OASISOccProfile?code={noc_code}.00&version=2025.0"
    try:
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code == 200:
            desc = _extract_profile_description(resp.text)
            if desc:
                result["description"] = desc
                return result
    except Exception:
        pass

    # .00 failed — look for sub-profiles on the hierarchy page
    try:
        hierarchy_html = _fetch_hierarchy_page()
        if not hierarchy_html:
            return result

        subs = _find_sub_profiles(noc_code, hierarchy_html)
        for sub in subs:
            sub_url = (
                f"{OASIS_BASE_URL}/OASIS/OASISOccProfile"
                f"?code={sub['code']}&version=2025.0"
            )
            try:
                sub_resp = requests.get(sub_url, verify=False, timeout=15)
                desc = None
                if sub_resp.status_code == 200:
                    desc = _extract_profile_description(sub_resp.text)
            except Exception:
                desc = None
            result["sub_profiles"].append({
                "code": sub["code"],
                "title": sub["title"],
                "description": desc,
            })
    except Exception:
        pass

    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_noc_unit_profile(noc_code: str) -> dict:
    """Fetch the unit group profile from the NOC Structure page.

    URL: https://noc.esdc.gc.ca/Structure/NOCProfile?GocTemplateCulture=en-CA&code=XXXXX&version=2021.0

    Returns:
        {
            "title": "Elementary school and kindergarten teachers",
            "example_titles": ["Kindergarten teacher", ...],
            "main_duties_intro": "This group performs...",
            "main_duties": ["Prepare courses...", ...],
            "employment_requirements": ["A bachelor's...", ...],
            "additional_information": ["...", ...],
            "exclusions": ["...", ...],
        }
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = (
        f"{OASIS_BASE_URL}/Structure/NOCProfile"
        f"?GocTemplateCulture=en-CA&code={noc_code}&version=2021.0"
    )
    result = {
        "title": "",
        "example_titles": [],
        "main_duties_intro": "",
        "main_duties": [],
        "employment_requirements": [],
        "additional_information": [],
        "exclusions": [],
    }

    try:
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title from h2: "41221  –  Elementary school and ..."
        h2 = soup.find("h2")
        if h2:
            raw = h2.get_text(strip=True)
            title = re.sub(r"^\d{5}\s*[–—-]\s*", "", raw)
            result["title"] = title

        # Find the Profile panel
        profile_h3 = soup.find("h3", string=lambda t: t and t.strip() == "Profile")
        if not profile_h3:
            return result

        panel_heading = profile_h3.find_parent("header")
        if not panel_heading:
            return result
        panel = panel_heading.find_parent(class_="panel")
        if not panel:
            return result
        body = panel.find("div", class_="panel-body", recursive=False)
        if not body:
            return result

        # Parse each sub-section
        for section in body.find_all("section", class_="panel"):
            h4 = section.find("h4")
            section_name = h4.get_text(strip=True).lower() if h4 else ""
            section_body = section.find("div", class_="panel-body")
            if not section_body:
                continue

            if "title" in section_name:
                example_div = section_body.find("div", class_="ExampleTitles")
                if example_div:
                    result["example_titles"] = [
                        li.get_text(strip=True)
                        for li in example_div.find_all("li")
                    ]
            elif "main duties" in section_name:
                h5 = section_body.find("h5")
                if h5:
                    result["main_duties_intro"] = h5.get_text(strip=True)
                result["main_duties"] = [
                    li.get_text(strip=True)
                    for li in section_body.find_all("li")
                ]
            elif "employment" in section_name:
                result["employment_requirements"] = [
                    li.get_text(strip=True)
                    for li in section_body.find_all("li")
                ]
            elif "additional" in section_name:
                items = [
                    li.get_text(strip=True)
                    for li in section_body.find_all("li")
                ]
                if not items:
                    items = [
                        p.get_text(strip=True)
                        for p in section_body.find_all("p")
                        if p.get_text(strip=True)
                    ]
                result["additional_information"] = items
            elif "exclusion" in section_name:
                result["exclusions"] = [
                    li.get_text(strip=True)
                    for li in section_body.find_all("li")
                ]

    except Exception:
        pass

    return result


# ─── Job Bank Skills / Competencies ───────────────────────────────────

JOBBANK_BASE = "https://www.jobbank.gc.ca"

# Map province names (from GEO_OPTIONS) to Job Bank location codes
_GEO_TO_JOBBANK = {
    "Canada": "ca",
    "Newfoundland and Labrador": "nl",
    "Prince Edward Island": "pe",
    "Nova Scotia": "ns",
    "New Brunswick": "nb",
    "Quebec": "qc",
    "Ontario": "on",
    "Manitoba": "mb",
    "Saskatchewan": "sk",
    "Alberta": "ab",
    "British Columbia": "bc",
    "Yukon": "yt",
    "Northwest Territories": "nt",
    "Nunavut": "nu",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _lookup_concordance_id(noc21_code: str) -> int | None:
    """Look up the Job Bank concordance_id for a NOC 2021 5-digit code.

    Uses the Job Bank Solr autocomplete API. Picks the first example title.
    """
    url = (
        f"{JOBBANK_BASE}/core/ta-jobtitle_en/select"
        f"?q={noc21_code}&wt=json&rows=50&fq=noc_job_title_type_id:1"
    )
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        docs = data.get("response", {}).get("docs", [])
        # Prefer example titles (example_ind == "1")
        for doc in docs:
            if doc.get("noc21_code") == noc21_code and doc.get("example_ind") == "1":
                return int(doc["noc_job_title_concordance_id"])
        # Fallback: any match with matching noc21_code
        for doc in docs:
            if doc.get("noc21_code") == noc21_code:
                return int(doc["noc_job_title_concordance_id"])
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_jobbank_skills(noc21_code: str, geo: str = "Canada") -> dict:
    """Fetch skills/competencies from Job Bank for a NOC 2021 code.

    URL: https://www.jobbank.gc.ca/marketreport/skills/{concordance_id}/{location}

    Returns:
        {
            "title": "Kindergarten Teacher",
            "skills": [{"name": "Social Perceptiveness", "level": "5 - Highest Level"}, ...],
            "work_styles": [{"name": "Concern for Others", "level": "5 - Extremely important"}, ...],
            "knowledge": [{"name": "Teaching", "level": "3 - Advanced Level"}, ...],
        }
    """
    result = {"title": "", "skills": [], "work_styles": [], "knowledge": []}

    concordance_id = _lookup_concordance_id(noc21_code)
    if not concordance_id:
        return result

    location = _GEO_TO_JOBBANK.get(geo, "ca")
    url = f"{JOBBANK_BASE}/marketreport/skills/{concordance_id}/{location}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title from page title: "Kindergarten Teacher in Canada | Skills"
        if soup.title:
            raw_title = soup.title.get_text(strip=True)
            title = re.sub(r"\s+in\s+.+$", "", raw_title)
            result["title"] = title

        # Extract all tables — they appear in order: Skills, Work Styles, Knowledge
        tables = soup.find_all("table")
        section_keys = ["skills", "work_styles", "knowledge"]

        for i, table in enumerate(tables):
            if i >= len(section_keys):
                break
            key = section_keys[i]
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    name = tds[0].get_text(strip=True)
                    level = tds[1].get_text(strip=True)
                    if name:
                        result[key].append({"name": name, "level": level})

    except Exception:
        pass

    return result


# ─── Job Bank Wages ──────────────────────────────────────────────────

# Province names → uppercase Job Bank location codes for wage URLs
_GEO_TO_JOBBANK_WAGE = {
    "Canada": "CA",
    "Newfoundland and Labrador": "NL",
    "Prince Edward Island": "PE",
    "Nova Scotia": "NS",
    "New Brunswick": "NB",
    "Quebec": "QC",
    "Ontario": "ON",
    "Manitoba": "MB",
    "Saskatchewan": "SK",
    "Alberta": "AB",
    "British Columbia": "BC",
    "Yukon": "YT",
    "Northwest Territories": "NT",
    "Nunavut": "NU",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_jobbank_wages(noc21_code: str, geo: str = "Canada") -> dict:
    """Fetch wage data from Job Bank for a NOC 2021 code.

    URL pattern: /marketreport/wages-occupation/{concordance_id}/{location}
    Returns:
        {"title": "...",
         "wages": {"low": 30.50, "median": 48.08, "high": 72.12},
         "community": [{"area": "Toronto", "low": 27.0, "median": 51.28, "high": 72.12}, ...]}
    """
    result = {"title": "", "wages": {}, "community": []}
    concordance_id = _lookup_concordance_id(noc21_code)
    if not concordance_id:
        return result

    location = _GEO_TO_JOBBANK_WAGE.get(geo, "CA")
    url = f"{JOBBANK_BASE}/marketreport/wages-occupation/{concordance_id}/{location}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return result
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title from page heading
        if soup.title:
            raw_title = soup.title.get_text(strip=True)
            title = re.sub(r"\s+in\s+.+$", "", raw_title)
            result["title"] = title

        # Parse wage table — area name is in a <th> per row,
        # wage values in the first 3 <td> elements (low, median, high).
        tables = soup.find_all("table")

        def _parse_wage_text(txt):
            txt = txt.strip().replace("$", "").replace(",", "")
            try:
                return float(txt)
            except (ValueError, TypeError):
                return None

        for table in tables:
            for row in table.find_all("tr"):
                th = row.find("th")
                tds = row.find_all("td")
                if th is None or len(tds) < 3:
                    continue
                area = th.get_text(strip=True)
                low = _parse_wage_text(tds[0].get_text())
                median = _parse_wage_text(tds[1].get_text())
                high = _parse_wage_text(tds[2].get_text())

                if low is None or median is None or high is None:
                    continue

                entry = {"area": area, "low": low, "median": median, "high": high}

                # First row matching the selected province is the summary
                if not result["wages"] and (
                    geo.lower() in area.lower()
                    or area.lower() in ("canada", geo.lower())
                ):
                    result["wages"] = {"low": low, "median": median, "high": high}
                else:
                    result["community"].append(entry)

        # Remove trailing "Canada" row from community if present
        if result["community"] and result["community"][-1]["area"].lower() == "canada":
            result["community"].pop()

        # Fallback: use first community row as summary
        if not result["wages"] and result["community"]:
            first = result["community"].pop(0)
            result["wages"] = {"low": first["low"], "median": first["median"], "high": first["high"]}

    except Exception:
        pass

    return result
