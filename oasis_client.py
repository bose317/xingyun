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
