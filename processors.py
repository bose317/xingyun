"""Data processors: build coordinates and query StatCan API for each analysis."""

import streamlit as st

from config import (
    TABLES,
    LABOUR_FORCE_GEO, LABOUR_FORCE_FIELDS, LABOUR_FORCE_STATUS,
    INCOME_GEO, INCOME_FIELDS, INCOME_STATS,
    UNEMP_GEO, UNEMP_INDICATOR, UNEMP_EDU,
    JOB_VAC_GEO, JOB_VAC_CHAR, JOB_VAC_STAT,
    GRAD_GEO, GRAD_FIELDS, GRAD_STATS,
    GRAD_CIP_GEO, GRAD_CIP_QUAL, GRAD_CIP_STATS,
    GRAD_CIP_BROAD_FIELDS, GRAD_CIP_SUBFIELDS, CIP_PREFIX_TO_GRAD_CIP,
    NOC_DIST_CIP_FIELDS, NOC_DIST_CIP_SUBFIELDS,
    NOC_BROAD_CATEGORIES, NOC_SUBMAJOR_GROUPS, NOC_DIST_STATS, NOC_DIST_EDU,
    NOC_2DIGIT_TO_5DIGIT, NOC_5DIGIT_NAMES,
    NOC_INCOME_AGE, NOC_INCOME_STATS as NOC_INC_STATS,
    FIELD_OPTIONS, EDUCATION_OPTIONS,
)
from data_client import StatCanClient


def _coord(parts: list[int], total: int = 10) -> str:
    """Build a 10-position coordinate string, padding with 0s."""
    padded = parts + [0] * (total - len(parts))
    return ".".join(str(p) for p in padded)


def _extract_value(coord_map: dict, coord: str) -> float | None:
    """Extract the latest value from a coordinate map entry."""
    obj = coord_map.get(coord)
    if obj and obj.get("vectorDataPoint"):
        return obj["vectorDataPoint"][0].get("value")
    return None


def _extract_series(coord_map: dict, coord: str) -> list[dict]:
    """Extract time series from a coordinate map entry."""
    obj = coord_map.get(coord)
    if not obj or not obj.get("vectorDataPoint"):
        return []
    return [
        {"date": dp["refPer"], "value": dp["value"]}
        for dp in obj["vectorDataPoint"]
        if dp.get("value") is not None
    ]


# ─── Tab 1: Employment Overview (table 98100445) ────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_labour_force(field_name: str, subfield_name: str | None, education: str, geo: str) -> dict:
    from data_client import get_client
    client = get_client()
    pid = TABLES["labour_force"]

    geo_id = LABOUR_FORCE_GEO.get(geo, 1)
    edu_id = EDUCATION_OPTIONS.get(education, {}).get("labour_force", 12)
    field_info = FIELD_OPTIONS.get(field_name, {})

    if subfield_name and subfield_name in field_info.get("subfields", {}):
        field_id = field_info["subfields"][subfield_name].get("labour_force", field_info.get("labour_force", 1))
    else:
        field_id = field_info.get("labour_force", 1)

    # geo.edu.loc(1).age(5=25-64).gender(1).field.status.0.0.0
    def make_coord(fid, status_id):
        return _coord([geo_id, edu_id, 1, 5, 1, fid, status_id])

    batch = []
    # User's rates
    rate_coords = {}
    for rate_name in ["Employment rate", "Unemployment rate", "Participation rate"]:
        c = make_coord(field_id, LABOUR_FORCE_STATUS[rate_name])
        rate_coords[rate_name] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    # All fields comparison
    field_coords = {}
    emp_status = LABOUR_FORCE_STATUS["Employment rate"]
    for fname, fid in LABOUR_FORCE_FIELDS.items():
        if fname == "Total":
            continue
        c = make_coord(fid, emp_status)
        field_coords[fname] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    coord_map = client.query_batch(batch)

    summary = {}
    for rate_name, c in rate_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            summary[rate_name.lower().replace(" ", "_")] = round(val, 1)

    comparison = []
    for fname, c in field_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            comparison.append({"field": fname, "employment_rate": round(val, 1)})
    comparison.sort(key=lambda x: x["employment_rate"])

    return {"summary": summary, "comparison": comparison, "user_field": field_name}


# ─── Tab 2: Income Analysis (table 98100409) ────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_income(field_name: str, subfield_name: str | None, education: str, geo: str) -> dict:
    from data_client import get_client
    client = get_client()
    pid = TABLES["income"]

    geo_id = INCOME_GEO.get(geo, 1)
    edu_id = EDUCATION_OPTIONS.get(education, {}).get("income", 12)
    field_info = FIELD_OPTIONS.get(field_name, {})

    if subfield_name and subfield_name in field_info.get("subfields", {}):
        field_id = field_info["subfields"][subfield_name].get("income", field_info.get("income", 1))
    else:
        field_id = field_info.get("income", 1)

    # geo.gender(1).age(5=25-64).edu.work(5=full-year-ft).year(1=2020).field.stat.0.0
    batch = []

    # User's income
    user_coords = {}
    for stat_name, key in [("Median employment income", "median_income"), ("Average employment income", "average_income")]:
        c = _coord([geo_id, 1, 5, edu_id, 5, 1, field_id, INCOME_STATS[stat_name]])
        user_coords[key] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    # Ranking across fields
    rank_coords = {}
    median_stat = INCOME_STATS["Median employment income"]
    for fname, fid in INCOME_FIELDS.items():
        if fname == "Total":
            continue
        c = _coord([geo_id, 1, 5, edu_id, 5, 1, fid, median_stat])
        rank_coords[fname] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    # Income by education level
    edu_levels = {
        "High school diploma": 3,
        "Apprenticeship/trades": 6,
        "College/CEGEP": 9,
        "Bachelor's degree": 12,
        "Master's degree": 15,
        "Earned doctorate": 16,
    }
    edu_coords = {}
    for ename, eid in edu_levels.items():
        c = _coord([geo_id, 1, 5, eid, 5, 1, field_id, median_stat])
        edu_coords[ename] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    coord_map = client.query_batch(batch)

    summary = {}
    for key, c in user_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            summary[key] = round(val, 0)

    ranking = []
    for fname, c in rank_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            ranking.append({"field": fname, "median_income": round(val, 0)})
    ranking.sort(key=lambda x: x["median_income"])

    by_education = []
    for ename, c in edu_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            by_education.append({"education": ename, "median_income": round(val, 0)})

    return {"summary": summary, "ranking": ranking, "by_education": by_education, "user_field": field_name}


# ─── Tab 3: Unemployment Trends (table 14100020) ────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_unemployment_trends(education: str, geo: str) -> dict:
    from data_client import get_client
    client = get_client()
    pid = TABLES["unemployment_trends"]

    geo_id = UNEMP_GEO.get(geo, 1)
    indicator_id = UNEMP_INDICATOR["Unemployment rate"]

    # geo.indicator.edu.gender(1).age(3=25+).0.0.0.0.0
    batch = []
    edu_coords = {}
    for ename, eid in UNEMP_EDU.items():
        c = _coord([geo_id, indicator_id, eid, 1, 3])
        edu_coords[ename] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 36})

    coord_map = client.query_batch(batch)

    trends = {}
    for ename, c in edu_coords.items():
        series = _extract_series(coord_map, c)
        if series:
            # Use year only for annual data
            for d in series:
                d["date"] = d["date"][:4]
            trends[ename] = series

    # Summary for user's education
    user_edu_id = EDUCATION_OPTIONS.get(education, {}).get("unemp")
    user_edu_name = None
    for ename, eid in UNEMP_EDU.items():
        if eid == user_edu_id:
            user_edu_name = ename
            break

    summary = {}
    if user_edu_name and user_edu_name in trends:
        user_series = trends[user_edu_name]
        if user_series:
            summary["current_rate"] = round(user_series[-1]["value"], 1)
            recent = user_series[-5:]
            summary["five_yr_avg"] = round(sum(d["value"] for d in recent) / len(recent), 1)

    return {"trends": trends, "summary": summary, "user_education": education}


# ─── Tab 4: Job Market (table 14100443) ─────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_job_vacancies(education: str, geo: str) -> dict:
    from data_client import get_client
    client = get_client()
    pid = TABLES["job_vacancies"]

    geo_id = JOB_VAC_GEO.get(geo, 1)
    char_id = EDUCATION_OPTIONS.get(education, {}).get("job_vac", 4)

    # geo.noc(1=all).char.stat.0.0.0.0.0.0
    batch = []

    vac_coord = _coord([geo_id, 1, char_id, JOB_VAC_STAT["Job vacancies"]])
    wage_coord = _coord([geo_id, 1, char_id, JOB_VAC_STAT["Average offered hourly wage"]])
    batch.append({"productId": pid, "coordinate": vac_coord, "latestN": 20})
    batch.append({"productId": pid, "coordinate": wage_coord, "latestN": 20})

    # By education level
    edu_coords = {}
    for char_name, cid in JOB_VAC_CHAR.items():
        if char_name == "All types":
            continue
        c = _coord([geo_id, 1, cid, JOB_VAC_STAT["Job vacancies"]])
        edu_coords[char_name] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    coord_map = client.query_batch(batch)

    vac_series = _extract_series(coord_map, vac_coord)
    wage_series = _extract_series(coord_map, wage_coord)

    # Merge vacancy and wage trends
    wage_map = {w["date"]: w["value"] for w in wage_series}
    trends = []
    for v in vac_series:
        trends.append({
            "date": v["date"],
            "vacancies": v["value"],
            "avg_wage": wage_map.get(v["date"]),
        })

    by_education = []
    for cname, c in edu_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            by_education.append({"education": cname, "vacancies": val})

    summary = {}
    if vac_series:
        summary["vacancies"] = int(vac_series[-1]["value"])
    if wage_series:
        summary["avg_wage"] = round(wage_series[-1]["value"], 2)

    return {"trends": trends, "by_education": by_education, "summary": summary}


# ─── Tab 5: Graduate Outcomes (table 37100283) ──────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_graduate_outcomes(field_name: str, education: str, geo: str) -> dict:
    from data_client import get_client
    client = get_client()
    pid = TABLES["graduate_outcomes"]

    geo_id = GRAD_GEO.get(geo, 1)
    grad_qual = EDUCATION_OPTIONS.get(education, {}).get("grad", 1)
    grad_field = FIELD_OPTIONS.get(field_name, {}).get("graduate", 1)

    # geo.qual.field.gender(1).age(1=15-64).student(1=all).char(4=reporting income).stat.0.0
    batch = []

    inc2_coord = _coord([geo_id, grad_qual, grad_field, 1, 1, 1, 4, GRAD_STATS["Median income 2yr after graduation"]])
    inc5_coord = _coord([geo_id, grad_qual, grad_field, 1, 1, 1, 4, GRAD_STATS["Median income 5yr after graduation"]])
    batch.append({"productId": pid, "coordinate": inc2_coord, "latestN": 1})
    batch.append({"productId": pid, "coordinate": inc5_coord, "latestN": 1})

    # Field comparison
    comp_coords = {}
    for fname, fid in GRAD_FIELDS.items():
        if fname == "Total":
            continue
        c = _coord([geo_id, grad_qual, fid, 1, 1, 1, 4, GRAD_STATS["Median income 2yr after graduation"]])
        comp_coords[fname] = c
        batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    coord_map = client.query_batch(batch)

    summary = {}
    trajectory = []

    val2 = _extract_value(coord_map, inc2_coord)
    if val2 is not None:
        summary["income_2yr"] = round(val2, 0)
        trajectory.append({"years_after": 2, "income": round(val2, 0)})

    val5 = _extract_value(coord_map, inc5_coord)
    if val5 is not None:
        summary["income_5yr"] = round(val5, 0)
        trajectory.append({"years_after": 5, "income": round(val5, 0)})

    if "income_2yr" in summary and "income_5yr" in summary and summary["income_2yr"] > 0:
        summary["growth_pct"] = round(
            (summary["income_5yr"] - summary["income_2yr"]) / summary["income_2yr"] * 100, 1
        )

    comparison = []
    for fname, c in comp_coords.items():
        val = _extract_value(coord_map, c)
        if val is not None:
            comparison.append({"field": fname, "income_2yr": round(val, 0)})

    return {"summary": summary, "trajectory": trajectory, "comparison": comparison}


# ─── Subfield Comparison (for within-field quadrant) ──────────────────


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_subfield_comparison(field_name: str, subfield_name: str | None, education: str, geo: str) -> dict:
    """Fetch employment rate + median income for all subfields under a broad field.

    For subfields that only have income data (no labour_force ID), inherit
    the employment rate from their parent 2-digit CIP or the broad field.
    """
    from data_client import get_client
    client = get_client()

    field_info = FIELD_OPTIONS.get(field_name, {})
    subfields = field_info.get("subfields", {})
    if not subfields:
        return {"subfields": [], "broad_field": field_name, "user_subfield": subfield_name}

    lf_pid = TABLES["labour_force"]
    inc_pid = TABLES["income"]

    geo_lf = LABOUR_FORCE_GEO.get(geo, 1)
    edu_lf = EDUCATION_OPTIONS.get(education, {}).get("labour_force", 12)
    emp_status = LABOUR_FORCE_STATUS["Employment rate"]

    geo_inc = INCOME_GEO.get(geo, 1)
    edu_inc = EDUCATION_OPTIONS.get(education, {}).get("income", 12)
    median_stat = INCOME_STATS["Median employment income"]

    batch = []

    # Broad field employment rate (fallback for subfields without labour_force data)
    broad_lf_id = field_info.get("labour_force", 1)
    broad_emp_coord = _coord([geo_lf, edu_lf, 1, 5, 1, broad_lf_id, emp_status])
    batch.append({"productId": lf_pid, "coordinate": broad_emp_coord, "latestN": 1})

    # Each subfield's employment rate and income
    sf_meta = {}  # name -> {emp_coord, inc_coord, lf_id}
    for sf_name, sf_ids in subfields.items():
        meta = {"name": sf_name}

        # Employment rate (only if labour_force ID exists)
        lf_id = sf_ids.get("labour_force")
        if lf_id is not None:
            emp_c = _coord([geo_lf, edu_lf, 1, 5, 1, lf_id, emp_status])
            meta["emp_coord"] = emp_c
            batch.append({"productId": lf_pid, "coordinate": emp_c, "latestN": 1})

        # Income (only if income ID exists)
        inc_id = sf_ids.get("income")
        if inc_id is not None:
            inc_c = _coord([geo_inc, 1, 5, edu_inc, 5, 1, inc_id, median_stat])
            meta["inc_coord"] = inc_c
            batch.append({"productId": inc_pid, "coordinate": inc_c, "latestN": 1})

        sf_meta[sf_name] = meta

    coord_map = client.query_batch(batch)

    broad_emp_rate = _extract_value(coord_map, broad_emp_coord)

    # Build a map of 2-digit CIP prefix -> employment rate (for inheritance)
    prefix_emp = {}
    for sf_name, meta in sf_meta.items():
        if "emp_coord" in meta:
            val = _extract_value(coord_map, meta["emp_coord"])
            if val is not None:
                # Extract 2-digit CIP prefix from name like "11. Computer..."
                prefix = sf_name.split(".")[0].strip()
                prefix_emp[prefix] = round(val, 1)

    # Assemble results
    result_subfields = []
    for sf_name, meta in sf_meta.items():
        entry = {"name": sf_name, "emp_exact": False}

        # Employment rate: exact or inherited
        if "emp_coord" in meta:
            val = _extract_value(coord_map, meta["emp_coord"])
            if val is not None:
                entry["employment_rate"] = round(val, 1)
                entry["emp_exact"] = True

        if "employment_rate" not in entry:
            # Try inheriting from parent 2-digit CIP
            prefix = sf_name.split(".")[0].strip()
            if prefix in prefix_emp:
                entry["employment_rate"] = prefix_emp[prefix]
            elif broad_emp_rate is not None:
                entry["employment_rate"] = round(broad_emp_rate, 1)

        # Income
        if "inc_coord" in meta:
            val = _extract_value(coord_map, meta["inc_coord"])
            if val is not None:
                entry["median_income"] = round(val, 0)

        # Only include if we have at least income data
        if "median_income" in entry and "employment_rate" in entry:
            result_subfields.append(entry)

    return {
        "subfields": result_subfields,
        "broad_field": field_name,
        "broad_emp_rate": round(broad_emp_rate, 1) if broad_emp_rate else None,
        "user_subfield": subfield_name,
    }


# ─── CIP Employment Distribution (table 37100280) ────────────────────


def _resolve_cip_to_grad_member(cip_code: str | None, broad_field: str) -> tuple[int, str]:
    """Resolve a 6-digit CIP code to the closest member ID in table 37100280.

    Returns (member_id, display_name).
    """
    if cip_code:
        prefix = cip_code.split(".")[0]
        if prefix in CIP_PREFIX_TO_GRAD_CIP:
            member_id = CIP_PREFIX_TO_GRAD_CIP[prefix]
            # Find display name
            for name, mid in GRAD_CIP_SUBFIELDS.items():
                if mid == member_id:
                    return member_id, name
            return member_id, f"CIP {prefix}"

    # Fall back to broad field
    member_id = GRAD_CIP_BROAD_FIELDS.get(broad_field, 1)
    return member_id, broad_field


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cip_employment_distribution(
    cip_code: str | None,
    broad_field: str,
    education: str,
    geo: str,
) -> dict:
    """Fetch 2yr and 5yr median income for the user's CIP and all broad CIP fields.

    Uses table 37-10-0280-01 (CIP alternative primary groupings).
    Returns data for a grouped bar chart comparing fields.
    """
    from data_client import get_client
    client = get_client()
    pid = TABLES["graduate_outcomes_cip"]

    geo_id = GRAD_CIP_GEO.get(geo, GRAD_CIP_GEO.get("Canada", 1))
    qual_id = EDUCATION_OPTIONS.get(education, {}).get("grad", 1)
    # Map education options to GRAD_CIP_QUAL keys
    qual_map = {
        "Bachelor's degree": 7,
        "Master's degree": 11,
        "Earned doctorate": 12,
        "College, CEGEP or other non-university certificate or diploma": 4,
        "Apprenticeship or trades certificate or diploma": 3,
        "High school diploma": 1,  # Use total as fallback
        "Degree in medicine, dentistry, veterinary medicine or optometry": 9,
        "University degree (any)": 7,
    }
    qual_id = qual_map.get(education, 1)

    stat_2yr = GRAD_CIP_STATS["Median income 2yr after graduation"]
    stat_5yr = GRAD_CIP_STATS["Median income 5yr after graduation"]
    stat_count = GRAD_CIP_STATS["Number of graduates"]

    user_field_id, user_field_name = _resolve_cip_to_grad_member(cip_code, broad_field)

    # Coordinate: geo.qual.field.gender(1).age(1=15-64).status(1=all).char(4=reporting income).stat.0.0
    def make_coord(field_id, stat_id):
        return _coord([geo_id, qual_id, field_id, 1, 1, 1, 4, stat_id])

    batch = []

    # User's own CIP field
    user_2yr_coord = make_coord(user_field_id, stat_2yr)
    user_5yr_coord = make_coord(user_field_id, stat_5yr)
    user_count_coord = make_coord(user_field_id, stat_count)
    batch.append({"productId": pid, "coordinate": user_2yr_coord, "latestN": 1})
    batch.append({"productId": pid, "coordinate": user_5yr_coord, "latestN": 1})
    batch.append({"productId": pid, "coordinate": user_count_coord, "latestN": 1})

    # All broad CIP fields for comparison
    field_coords = {}
    for fname, fid in GRAD_CIP_BROAD_FIELDS.items():
        if fname == "Total":
            continue
        c2 = make_coord(fid, stat_2yr)
        c5 = make_coord(fid, stat_5yr)
        cc = make_coord(fid, stat_count)
        field_coords[fname] = {"coord_2yr": c2, "coord_5yr": c5, "coord_count": cc}
        batch.append({"productId": pid, "coordinate": c2, "latestN": 1})
        batch.append({"productId": pid, "coordinate": c5, "latestN": 1})
        batch.append({"productId": pid, "coordinate": cc, "latestN": 1})

    # Sub-fields within the user's broad field for detailed view
    subfield_coords = {}
    for sf_name, sf_id in GRAD_CIP_SUBFIELDS.items():
        # Check if this sub-field belongs to the user's broad field
        # by checking if its parent ID matches
        broad_id = GRAD_CIP_BROAD_FIELDS.get(broad_field, 0)
        # Sub-fields are children: their IDs are between broad_id+1 and next broad_id
        broad_ids_sorted = sorted(GRAD_CIP_BROAD_FIELDS.values())
        idx = broad_ids_sorted.index(broad_id) if broad_id in broad_ids_sorted else -1
        if idx >= 0:
            next_broad = broad_ids_sorted[idx + 1] if idx + 1 < len(broad_ids_sorted) else 999
            if broad_id < sf_id < next_broad:
                c2 = make_coord(sf_id, stat_2yr)
                c5 = make_coord(sf_id, stat_5yr)
                cc = make_coord(sf_id, stat_count)
                subfield_coords[sf_name] = {"coord_2yr": c2, "coord_5yr": c5, "coord_count": cc}
                batch.append({"productId": pid, "coordinate": c2, "latestN": 1})
                batch.append({"productId": pid, "coordinate": c5, "latestN": 1})
                batch.append({"productId": pid, "coordinate": cc, "latestN": 1})

    coord_map = client.query_batch(batch)

    # Extract user's data
    user_summary = {}
    val2 = _extract_value(coord_map, user_2yr_coord)
    val5 = _extract_value(coord_map, user_5yr_coord)
    val_count = _extract_value(coord_map, user_count_coord)
    if val2 is not None:
        user_summary["income_2yr"] = round(val2, 0)
    if val5 is not None:
        user_summary["income_5yr"] = round(val5, 0)
    if val_count is not None:
        user_summary["graduate_count"] = int(val_count)
    if val2 and val5 and val2 > 0:
        user_summary["growth_pct"] = round((val5 - val2) / val2 * 100, 1)

    # Extract broad field comparison data
    broad_comparison = []
    for fname, coords in field_coords.items():
        v2 = _extract_value(coord_map, coords["coord_2yr"])
        v5 = _extract_value(coord_map, coords["coord_5yr"])
        vc = _extract_value(coord_map, coords["coord_count"])
        if v2 is not None or v5 is not None:
            entry = {"field": fname}
            if v2 is not None:
                entry["income_2yr"] = round(v2, 0)
            if v5 is not None:
                entry["income_5yr"] = round(v5, 0)
            if vc is not None:
                entry["graduate_count"] = int(vc)
            if v2 and v5 and v2 > 0:
                entry["growth_pct"] = round((v5 - v2) / v2 * 100, 1)
            broad_comparison.append(entry)
    broad_comparison.sort(key=lambda x: x.get("income_5yr", 0), reverse=True)

    # Extract sub-field data within user's broad field
    subfield_comparison = []
    for sf_name, coords in subfield_coords.items():
        v2 = _extract_value(coord_map, coords["coord_2yr"])
        v5 = _extract_value(coord_map, coords["coord_5yr"])
        vc = _extract_value(coord_map, coords["coord_count"])
        if v2 is not None or v5 is not None:
            entry = {"field": sf_name}
            if v2 is not None:
                entry["income_2yr"] = round(v2, 0)
            if v5 is not None:
                entry["income_5yr"] = round(v5, 0)
            if vc is not None:
                entry["graduate_count"] = int(vc)
            if v2 and v5 and v2 > 0:
                entry["growth_pct"] = round((v5 - v2) / v2 * 100, 1)
            subfield_comparison.append(entry)
    subfield_comparison.sort(key=lambda x: x.get("income_5yr", 0), reverse=True)

    return {
        "user_summary": user_summary,
        "user_field_name": user_field_name,
        "broad_field": broad_field,
        "broad_comparison": broad_comparison,
        "subfield_comparison": subfield_comparison,
    }


# ─── CIP → NOC Occupation Distribution (table 98100403) ──────────────


def _resolve_cip_to_noc_dist_member(cip_code: str | None, broad_field: str) -> tuple[int, str]:
    """Resolve a CIP code to the member ID in table 98100403.

    Returns (member_id, display_name).
    """
    if cip_code:
        prefix = cip_code.split(".")[0]
        if prefix in NOC_DIST_CIP_SUBFIELDS:
            return NOC_DIST_CIP_SUBFIELDS[prefix], f"CIP {prefix}"

    # Fall back to broad field
    member_id = NOC_DIST_CIP_FIELDS.get(broad_field, 1)
    return member_id, broad_field


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_noc_distribution(
    cip_code: str | None,
    broad_field: str,
    education: str,
) -> dict:
    """Fetch occupation (NOC) distribution for a given CIP field of study.

    Uses table 98-10-0403-01 (Occupation by major field of study).
    Returns % distribution across NOC broad categories and sub-major groups.
    Coordinate: geo(1).age(3=25-64).cip.edu.gender(1).noc.stat.0.0.0
    """
    from data_client import get_client
    client = get_client()
    pid = TABLES["cip_noc_distribution"]

    edu_id = NOC_DIST_EDU.get(education, NOC_DIST_EDU.get("Total", 1))
    # Map education option labels to table 98100403 education IDs
    edu_map = {
        "Bachelor's degree": 12,
        "Master's degree": 15,
        "Earned doctorate": 16,
        "College, CEGEP or other non-university certificate or diploma": 9,
        "Apprenticeship or trades certificate or diploma": 6,
        "High school diploma": 3,
        "Degree in medicine, dentistry, veterinary medicine or optometry": 14,
        "University degree (any)": 11,
    }
    edu_id = edu_map.get(education, 1)

    cip_id, cip_display = _resolve_cip_to_noc_dist_member(cip_code, broad_field)

    pct_stat = NOC_DIST_STATS["pct_distribution"]
    count_stat = NOC_DIST_STATS["count"]

    # Coordinate: geo(1).age(3=25-64).cip.edu.gender(1).noc.stat.0.0.0
    def make_coord(noc_id, stat_id):
        return _coord([1, 3, cip_id, edu_id, 1, noc_id, stat_id])

    batch = []

    # Query broad NOC categories (1-digit level) — % distribution
    broad_coords = {}
    for noc_name, noc_id in NOC_BROAD_CATEGORIES.items():
        c_pct = make_coord(noc_id, pct_stat)
        c_cnt = make_coord(noc_id, count_stat)
        broad_coords[noc_name] = {"pct_coord": c_pct, "count_coord": c_cnt}
        batch.append({"productId": pid, "coordinate": c_pct, "latestN": 1})
        batch.append({"productId": pid, "coordinate": c_cnt, "latestN": 1})

    # Query 2-digit NOC sub-major groups — % distribution
    submajor_coords = {}
    for noc_name, noc_id in NOC_SUBMAJOR_GROUPS.items():
        c_pct = make_coord(noc_id, pct_stat)
        c_cnt = make_coord(noc_id, count_stat)
        submajor_coords[noc_name] = {"pct_coord": c_pct, "count_coord": c_cnt}
        batch.append({"productId": pid, "coordinate": c_pct, "latestN": 1})
        batch.append({"productId": pid, "coordinate": c_cnt, "latestN": 1})

    # Also query "Occupation - not applicable" (member 2)
    na_pct_coord = make_coord(2, pct_stat)
    na_cnt_coord = make_coord(2, count_stat)
    batch.append({"productId": pid, "coordinate": na_pct_coord, "latestN": 1})
    batch.append({"productId": pid, "coordinate": na_cnt_coord, "latestN": 1})

    coord_map = client.query_batch(batch)

    # Extract broad NOC distribution
    broad_distribution = []
    for noc_name, coords in broad_coords.items():
        pct = _extract_value(coord_map, coords["pct_coord"])
        cnt = _extract_value(coord_map, coords["count_coord"])
        if pct is not None and pct > 0:
            entry = {"noc": noc_name, "percentage": round(pct, 1)}
            if cnt is not None:
                entry["count"] = int(cnt)
            broad_distribution.append(entry)
    broad_distribution.sort(key=lambda x: x["percentage"], reverse=True)

    # Extract sub-major group distribution
    submajor_distribution = []
    for noc_name, coords in submajor_coords.items():
        pct = _extract_value(coord_map, coords["pct_coord"])
        cnt = _extract_value(coord_map, coords["count_coord"])
        if pct is not None and pct > 0.1:  # Filter out very small groups
            entry = {"noc": noc_name, "percentage": round(pct, 1)}
            if cnt is not None:
                entry["count"] = int(cnt)
            submajor_distribution.append(entry)
    submajor_distribution.sort(key=lambda x: x["percentage"], reverse=True)

    # "Not applicable" percentage
    na_pct = _extract_value(coord_map, na_pct_coord)
    na_cnt = _extract_value(coord_map, na_cnt_coord)

    # ── Second pass: drill down to 5-digit NOC for significant 2-digit groups ──
    # Find 2-digit groups with > 1% to drill into
    significant_2digit = []
    for noc_name, coords in submajor_coords.items():
        pct = _extract_value(coord_map, coords["pct_coord"])
        if pct is not None and pct >= 1.0:
            # Find the member ID of this 2-digit group
            noc_id = NOC_SUBMAJOR_GROUPS.get(noc_name)
            if noc_id and noc_id in NOC_2DIGIT_TO_5DIGIT:
                significant_2digit.append(noc_id)

    detail_batch = []
    detail_coords = {}  # member_id -> coord
    for two_digit_id in significant_2digit:
        for five_digit_id in NOC_2DIGIT_TO_5DIGIT[two_digit_id]:
            c_pct = make_coord(five_digit_id, pct_stat)
            c_cnt = make_coord(five_digit_id, count_stat)
            detail_coords[five_digit_id] = {"pct_coord": c_pct, "count_coord": c_cnt}
            detail_batch.append({"productId": pid, "coordinate": c_pct, "latestN": 1})
            detail_batch.append({"productId": pid, "coordinate": c_cnt, "latestN": 1})

    detail_distribution = []
    if detail_batch:
        detail_map = client.query_batch(detail_batch)
        for mid, coords in detail_coords.items():
            pct = _extract_value(detail_map, coords["pct_coord"])
            cnt = _extract_value(detail_map, coords["count_coord"])
            if pct is not None and pct >= 0.3:  # Include occupations with at least 0.3%
                name = NOC_5DIGIT_NAMES.get(mid, f"NOC {mid}")
                entry = {"noc": name, "percentage": round(pct, 1)}
                if cnt is not None:
                    entry["count"] = int(cnt)
                detail_distribution.append(entry)
        detail_distribution.sort(key=lambda x: x["percentage"], reverse=True)

    return {
        "cip_field": cip_display,
        "broad_distribution": broad_distribution,
        "submajor_distribution": submajor_distribution,
        "detail_distribution": detail_distribution,
        "not_applicable_pct": round(na_pct, 1) if na_pct else None,
        "not_applicable_count": int(na_cnt) if na_cnt else None,
    }


# ─── NOC Gender Breakdown (table 98100403) ────────────────────────────


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_noc_gender_breakdown(
    noc_entries: list[dict],
    cip_code: str | None,
    broad_field: str,
    education: str,
    top_n: int = 5,
) -> list[dict]:
    """Fetch male/female count breakdown for top NOC occupations.

    noc_entries: list of dicts with 'noc' (name string) and 'count' keys,
                 as returned in detail_distribution or submajor_distribution.
    Returns list of dicts: {noc, count_total, count_male, count_female}.
    Coordinate: geo(1).age(3=25-64).cip.edu.gender.noc.stat.0.0.0
    """
    from data_client import get_client
    client = get_client()
    pid = TABLES["cip_noc_distribution"]

    edu_map = {
        "Bachelor's degree": 12,
        "Master's degree": 15,
        "Earned doctorate": 16,
        "College, CEGEP or other non-university certificate or diploma": 9,
        "Apprenticeship or trades certificate or diploma": 6,
        "High school diploma": 3,
        "Degree in medicine, dentistry, veterinary medicine or optometry": 14,
        "University degree (any)": 11,
    }
    edu_id = edu_map.get(education, 1)
    cip_id, _ = _resolve_cip_to_noc_dist_member(cip_code, broad_field)
    count_stat = NOC_DIST_STATS["count"]

    # Build a reverse lookup: NOC name → member ID
    # Combine submajor and 5-digit maps
    all_noc_ids = {}
    all_noc_ids.update(NOC_SUBMAJOR_GROUPS)
    all_noc_ids.update(NOC_5DIGIT_NAMES)  # This is id→name, we need name→id
    name_to_id = {}
    name_to_id.update({name: mid for name, mid in NOC_SUBMAJOR_GROUPS.items()})
    name_to_id.update({name: mid for mid, name in NOC_5DIGIT_NAMES.items()})

    entries = noc_entries[:top_n]

    def make_coord(gender_id, noc_id):
        return _coord([1, 3, cip_id, edu_id, gender_id, noc_id, count_stat])

    batch = []
    coord_keys = []  # (index, gender_label, coord)

    for i, entry in enumerate(entries):
        noc_name = entry["noc"]
        noc_id = name_to_id.get(noc_name)
        if not noc_id:
            continue
        for gender_id, gender_label in [(1, "total"), (2, "male"), (3, "female")]:
            c = make_coord(gender_id, noc_id)
            coord_keys.append((i, gender_label, c))
            batch.append({"productId": pid, "coordinate": c, "latestN": 1})

    if not batch:
        return []

    coord_map = client.query_batch(batch)

    # Collect results
    results_map = {}  # index → {total, male, female}
    for i, gender_label, c in coord_keys:
        val = _extract_value(coord_map, c)
        if i not in results_map:
            results_map[i] = {"noc": entries[i]["noc"], "total": None, "male": None, "female": None}
        results_map[i][gender_label] = int(val) if val is not None else None

    result = []
    for i in range(len(entries)):
        if i in results_map:
            r = results_map[i]
            result.append({
                "noc": r["noc"],
                "count_total": r["total"],
                "count_male": r["male"],
                "count_female": r["female"],
            })
    return result


# ─── NOC Income for Quadrant Bubble Chart (table 98100412) ────────────


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_noc_income_for_quadrant(
    noc_entries: list[dict],
    cip_code: str | None,
    broad_field: str,
    education: str,
) -> list[dict]:
    """Fetch income data for NOC occupations to build a quadrant bubble chart.

    For each NOC in noc_entries (which has 'noc', 'percentage', and member ID embedded
    in NOC_5DIGIT_NAMES), queries table 98-10-0412-01 for:
    - Median income at age 25-64 (Y-axis)
    - Median income at age 15-24 (for computing growth → bubble radius)

    Coordinate format: geo(1).gender(1).age.edu.cip.work_activity(1).noc.income_stat(3=median).0.0

    Returns list of dicts: [{noc, percentage, income, income_young, income_growth, member_id}, ...]
    """
    if not noc_entries:
        return []

    from data_client import get_client
    client = get_client()
    pid = TABLES["noc_income"]

    # Resolve CIP member ID (63-member dimension, same as table 37100280)
    cip_id, _ = _resolve_cip_to_grad_member(cip_code, broad_field)

    # Education mapping (same as NOC distribution)
    edu_map = {
        "Bachelor's degree": 12,
        "Master's degree": 15,
        "Earned doctorate": 16,
        "College, CEGEP or other non-university certificate or diploma": 9,
        "Apprenticeship or trades certificate or diploma": 6,
        "High school diploma": 3,
        "Degree in medicine, dentistry, veterinary medicine or optometry": 14,
        "University degree (any)": 11,
    }
    edu_id = edu_map.get(education, 1)

    age_young = NOC_INCOME_AGE["15-24"]
    age_mature = NOC_INCOME_AGE["25-64"]
    median_stat = NOC_INC_STATS["Median employment income"]

    # Reverse lookup: NOC name → member ID
    name_to_id = {v: k for k, v in NOC_5DIGIT_NAMES.items()}

    # Coordinate: geo(1).gender(1).age.edu.cip.work_activity(1).noc.income_stat.0.0
    def make_coord(age_id, noc_member_id):
        return _coord([1, 1, age_id, edu_id, cip_id, 1, noc_member_id, median_stat])

    batch = []
    noc_query_map = {}  # member_id -> {entry, coord_young, coord_mature}

    for entry in noc_entries:
        noc_name = entry["noc"]
        member_id = name_to_id.get(noc_name)
        if member_id is None:
            continue

        c_young = make_coord(age_young, member_id)
        c_mature = make_coord(age_mature, member_id)
        noc_query_map[member_id] = {
            "entry": entry,
            "coord_young": c_young,
            "coord_mature": c_mature,
        }
        batch.append({"productId": pid, "coordinate": c_young, "latestN": 1})
        batch.append({"productId": pid, "coordinate": c_mature, "latestN": 1})

    if not batch:
        return []

    coord_map = client.query_batch(batch)

    results = []
    for member_id, info in noc_query_map.items():
        entry = info["entry"]
        income_young = _extract_value(coord_map, info["coord_young"])
        income_mature = _extract_value(coord_map, info["coord_mature"])

        if income_mature is not None and income_mature > 0:
            income_growth = None
            if income_young is not None and income_young > 0:
                income_growth = round(
                    (income_mature - income_young) / income_young * 100, 1
                )

            results.append({
                "noc": entry["noc"],
                "percentage": entry["percentage"],
                "count": entry.get("count"),
                "income": round(income_mature, 0),
                "income_young": round(income_young, 0) if income_young else None,
                "income_growth": income_growth,
                "member_id": member_id,
            })

    return results
