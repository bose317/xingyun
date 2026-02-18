"""Data processors: build coordinates and query StatCan API for each analysis."""

import streamlit as st

from config import (
    TABLES,
    LABOUR_FORCE_GEO, LABOUR_FORCE_FIELDS, LABOUR_FORCE_STATUS,
    INCOME_GEO, INCOME_FIELDS, INCOME_STATS,
    UNEMP_GEO, UNEMP_INDICATOR, UNEMP_EDU,
    JOB_VAC_GEO, JOB_VAC_CHAR, JOB_VAC_STAT,
    GRAD_GEO, GRAD_FIELDS, GRAD_STATS,
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
