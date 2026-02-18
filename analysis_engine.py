"""Deep career analysis engine — pure computation, no Streamlit/Plotly.

Takes cached Page 2 data and computes:
A. Composite Career Prospect Score (0-100)
B. Trend Analysis & 3-Year Forecast
C. Income Growth Projection
D. Career Stability / Risk Assessment
E. Education ROI
F. Field Competitiveness
"""

import math

import numpy as np


# ── A. Composite Career Prospect Score ─────────────────────────────


def _percentile_score(value: float, all_values: list[float]) -> float:
    """Return 0-100 percentile score of value within all_values."""
    if not all_values or value is None:
        return 50.0
    sorted_vals = sorted(all_values)
    n = len(sorted_vals)
    if n == 1:
        return 50.0
    count_below = sum(1 for v in sorted_vals if v < value)
    return min(100.0, (count_below / (n - 1)) * 100)


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def compute_composite_score(page2_data: dict) -> dict:
    """Compute weighted composite career prospect score (0-100).

    Sub-scores (each 0-100):
    - Employment (25%): employment rate percentile vs all fields
    - Income (25%): median income percentile vs all fields
    - Trend (20%): unemployment trend slope (negative = improving)
    - Demand (15%): job vacancy trend direction
    - Growth (15%): graduate income growth 2yr->5yr, benchmarked 0-50% -> 0-100
    """
    components = {}

    # Employment sub-score
    labour = page2_data.get("labour_force", {})
    emp_rate = labour.get("summary", {}).get("employment_rate")
    comparison = labour.get("comparison", [])
    all_emp_rates = [c["employment_rate"] for c in comparison if c.get("employment_rate") is not None]
    if emp_rate is not None and all_emp_rates:
        components["Employment"] = round(_percentile_score(emp_rate, all_emp_rates), 1)
    else:
        components["Employment"] = 50.0

    # Income sub-score
    income = page2_data.get("income", {})
    median_inc = income.get("summary", {}).get("median_income")
    ranking = income.get("ranking", [])
    all_incomes = [r["median_income"] for r in ranking if r.get("median_income") is not None]
    if median_inc is not None and all_incomes:
        components["Income"] = round(_percentile_score(median_inc, all_incomes), 1)
    else:
        components["Income"] = 50.0

    # Trend sub-score (unemployment slope — negative = improving)
    unemp = page2_data.get("unemployment", {})
    user_edu = unemp.get("user_education", "")
    trends = unemp.get("trends", {})
    # Find the user's education series
    user_series = _find_user_unemployment_series(trends, user_edu)
    if user_series and len(user_series) >= 3:
        values = [d["value"] for d in user_series]
        x = np.arange(len(values), dtype=float)
        slope, _ = np.polyfit(x, values, 1)
        # Slope range: roughly -2 to +2 per year. Map to 0-100 (negative = better)
        trend_score = max(0.0, min(100.0, 50 - slope * 25))
        components["Trend"] = round(trend_score, 1)
    else:
        components["Trend"] = 50.0

    # Demand sub-score (job vacancy trend direction)
    vacancies = page2_data.get("job_vacancies", {})
    vac_trends = vacancies.get("trends", [])
    if vac_trends and len(vac_trends) >= 4:
        vac_values = [t["vacancies"] for t in vac_trends if t.get("vacancies") is not None]
        if len(vac_values) >= 4:
            mid = len(vac_values) // 2
            older_avg = np.mean(vac_values[:mid])
            recent_avg = np.mean(vac_values[mid:])
            if older_avg > 0:
                change_pct = (recent_avg - older_avg) / older_avg * 100
                # Map -50% to +50% -> 0 to 100
                demand_score = max(0.0, min(100.0, 50 + change_pct))
            else:
                demand_score = 50.0
            components["Demand"] = round(demand_score, 1)
        else:
            components["Demand"] = 50.0
    else:
        components["Demand"] = 50.0

    # Growth sub-score (graduate income growth 2yr->5yr)
    grad = page2_data.get("graduate_outcomes", {})
    growth_pct = grad.get("summary", {}).get("growth_pct")
    if growth_pct is not None:
        # Benchmark: 0-50% growth -> 0-100 score
        growth_score = max(0.0, min(100.0, growth_pct * 2))
        components["Growth"] = round(growth_score, 1)
    else:
        components["Growth"] = 50.0

    # Weighted total
    weights = {
        "Employment": 0.25,
        "Income": 0.25,
        "Trend": 0.20,
        "Demand": 0.15,
        "Growth": 0.15,
    }
    total = sum(components[k] * weights[k] for k in weights)
    total = round(total, 1)

    return {
        "total": total,
        "components": components,
        "grade": _grade(total),
    }


def _find_user_unemployment_series(trends: dict, user_education: str) -> list[dict]:
    """Find the unemployment series matching user's education level."""
    from config import EDUCATION_OPTIONS, UNEMP_EDU

    user_edu_id = EDUCATION_OPTIONS.get(user_education, {}).get("unemp")
    for ename, eid in UNEMP_EDU.items():
        if eid == user_edu_id and ename in trends:
            return trends[ename]
    # Fallback: first available
    if trends:
        return next(iter(trends.values()))
    return []


# ── B. Trend Analysis & 3-Year Forecast ───────────────────────────


def _moving_average(values: list[float], window: int = 3) -> list[float]:
    """Simple moving average with given window."""
    if len(values) < window:
        return values[:]
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        result.append(float(np.mean(values[start:i + 1])))
    return result


def compute_unemployment_forecast(page2_data: dict) -> dict:
    """Forecast unemployment rate 3 years ahead using linear regression.

    Returns: {dates, values, smoothed, forecast_dates, forecast_values,
              upper_band, lower_band, slope, interpretation}
    """
    unemp = page2_data.get("unemployment", {})
    user_edu = unemp.get("user_education", "")
    trends = unemp.get("trends", {})
    series = _find_user_unemployment_series(trends, user_edu)

    if not series or len(series) < 3:
        return {"error": "Insufficient unemployment data for forecasting"}

    dates = [d["date"] for d in series]
    values = [d["value"] for d in series]
    smoothed = _moving_average(values, window=3)

    # Linear regression on smoothed values
    x = np.arange(len(smoothed), dtype=float)
    coeffs = np.polyfit(x, smoothed, 1)
    slope, intercept = coeffs

    # Residuals for confidence band
    fitted = np.polyval(coeffs, x)
    residuals = np.array(smoothed) - fitted
    std_residual = float(np.std(residuals))

    # Forecast 3 years ahead
    n = len(smoothed)
    forecast_x = np.arange(n, n + 3, dtype=float)
    forecast_values = [max(0.0, round(float(np.polyval(coeffs, fx)), 2)) for fx in forecast_x]

    # Generate forecast dates (extrapolate year labels)
    try:
        last_year = int(dates[-1][:4])
        forecast_dates = [str(last_year + i + 1) for i in range(3)]
    except (ValueError, IndexError):
        forecast_dates = [f"Y+{i + 1}" for i in range(3)]

    upper_band = [round(v + std_residual, 2) for v in forecast_values]
    lower_band = [max(0.0, round(v - std_residual, 2)) for v in forecast_values]

    if slope < -0.1:
        interpretation = "Improving — unemployment trending downward"
    elif slope > 0.1:
        interpretation = "Worsening — unemployment trending upward"
    else:
        interpretation = "Stable — unemployment relatively flat"

    return {
        "dates": dates,
        "values": values,
        "smoothed": smoothed,
        "forecast_dates": forecast_dates,
        "forecast_values": forecast_values,
        "upper_band": upper_band,
        "lower_band": lower_band,
        "slope": round(float(slope), 4),
        "std_residual": round(std_residual, 4),
        "interpretation": interpretation,
    }


def compute_vacancy_forecast(page2_data: dict) -> dict:
    """Forecast job vacancies using linear regression on quarterly data.

    Returns: {dates, values, smoothed, forecast_dates, forecast_values,
              upper_band, lower_band, slope, interpretation}
    """
    vac = page2_data.get("job_vacancies", {})
    vac_trends = vac.get("trends", [])

    if not vac_trends or len(vac_trends) < 4:
        return {"error": "Insufficient vacancy data for forecasting"}

    dates = [t["date"] for t in vac_trends]
    values = [t["vacancies"] for t in vac_trends if t.get("vacancies") is not None]
    valid_dates = [t["date"] for t in vac_trends if t.get("vacancies") is not None]

    if len(values) < 4:
        return {"error": "Insufficient vacancy data for forecasting"}

    smoothed = _moving_average(values, window=3)

    x = np.arange(len(smoothed), dtype=float)
    coeffs = np.polyfit(x, smoothed, 1)
    slope, intercept = coeffs

    fitted = np.polyval(coeffs, x)
    residuals = np.array(smoothed) - fitted
    std_residual = float(np.std(residuals))

    # Forecast 3 quarters ahead (vacancy data is quarterly)
    n = len(smoothed)
    forecast_x = np.arange(n, n + 3, dtype=float)
    forecast_values = [max(0.0, round(float(np.polyval(coeffs, fx)), 0)) for fx in forecast_x]

    forecast_dates = [f"Q+{i + 1}" for i in range(3)]

    upper_band = [round(v + std_residual, 0) for v in forecast_values]
    lower_band = [max(0.0, round(v - std_residual, 0)) for v in forecast_values]

    if slope > 100:
        interpretation = "Growing — job vacancies increasing"
    elif slope < -100:
        interpretation = "Declining — job vacancies decreasing"
    else:
        interpretation = "Stable — job vacancies relatively flat"

    return {
        "dates": valid_dates,
        "values": values,
        "smoothed": smoothed,
        "forecast_dates": forecast_dates,
        "forecast_values": forecast_values,
        "upper_band": upper_band,
        "lower_band": lower_band,
        "slope": round(float(slope), 2),
        "std_residual": round(std_residual, 2),
        "interpretation": interpretation,
    }


# ── C. Income Growth Projection ───────────────────────────────────


def compute_income_projection(page2_data: dict) -> dict:
    """Project income to year 10 and 15 using logarithmic curve fit.

    Fits: income = a * ln(year) + b using 2yr and 5yr graduate income data.
    Returns: {data_points, projected_points, curve_years, curve_incomes,
              formula, field_avg_2yr, field_avg_5yr}
    """
    grad = page2_data.get("graduate_outcomes", {})
    summary = grad.get("summary", {})
    income_2yr = summary.get("income_2yr")
    income_5yr = summary.get("income_5yr")

    if income_2yr is None or income_5yr is None:
        return {"error": "Insufficient graduate income data for projection"}

    if income_2yr <= 0:
        return {"error": "Invalid income data (2yr income <= 0)"}

    # Fit logarithmic curve: income = a * ln(year) + b
    # Using 2 data points: (2, income_2yr) and (5, income_5yr)
    ln2 = math.log(2)
    ln5 = math.log(5)
    a = (income_5yr - income_2yr) / (ln5 - ln2)
    b = income_2yr - a * ln2

    # Generate smooth curve from year 1 to 15
    curve_years = list(range(1, 16))
    curve_incomes = [round(a * math.log(y) + b, 0) for y in curve_years]

    # Project specific years
    projected = {}
    for y in [10, 15]:
        projected[y] = round(a * math.log(y) + b, 0)

    # Field average comparison from graduate comparison data
    comparison = grad.get("comparison", [])
    field_avg_2yr = None
    if comparison:
        incomes = [c["income_2yr"] for c in comparison if c.get("income_2yr") is not None]
        if incomes:
            field_avg_2yr = round(sum(incomes) / len(incomes), 0)

    return {
        "data_points": [
            {"year": 2, "income": income_2yr},
            {"year": 5, "income": income_5yr},
        ],
        "projected_points": [
            {"year": 10, "income": projected[10]},
            {"year": 15, "income": projected[15]},
        ],
        "curve_years": curve_years,
        "curve_incomes": curve_incomes,
        "formula": {"a": round(a, 2), "b": round(b, 2)},
        "field_avg_2yr": field_avg_2yr,
    }


# ── D. Career Stability / Risk Assessment ─────────────────────────


def compute_risk_assessment(page2_data: dict) -> dict:
    """Assess career stability and risk.

    Metrics:
    - Volatility: coefficient of variation of unemployment time series
    - Income symmetry: median/average income ratio (<1 = inequality/risk)
    - Stability grade: A-F based on CV thresholds

    Returns: {volatility_cv, volatility_grade, income_symmetry, symmetry_grade,
              overall_grade, interpretation}
    """
    # Volatility from unemployment time series
    unemp = page2_data.get("unemployment", {})
    user_edu = unemp.get("user_education", "")
    trends = unemp.get("trends", {})
    series = _find_user_unemployment_series(trends, user_edu)

    volatility_cv = None
    volatility_grade = "N/A"
    if series and len(series) >= 3:
        values = [d["value"] for d in series]
        mean_val = float(np.mean(values))
        if mean_val > 0:
            volatility_cv = round(float(np.std(values) / mean_val) * 100, 1)
            # CV thresholds for stability: <10% A, <20% B, <30% C, <40% D, else F
            if volatility_cv < 10:
                volatility_grade = "A"
            elif volatility_cv < 20:
                volatility_grade = "B"
            elif volatility_cv < 30:
                volatility_grade = "C"
            elif volatility_cv < 40:
                volatility_grade = "D"
            else:
                volatility_grade = "F"

    # Income symmetry: median / average
    income = page2_data.get("income", {})
    median_inc = income.get("summary", {}).get("median_income")
    avg_inc = income.get("summary", {}).get("average_income")

    income_symmetry = None
    symmetry_grade = "N/A"
    if median_inc and avg_inc and avg_inc > 0:
        income_symmetry = round(median_inc / avg_inc, 3)
        # Closer to 1.0 = more symmetric/equal = better
        if income_symmetry >= 0.95:
            symmetry_grade = "A"
        elif income_symmetry >= 0.85:
            symmetry_grade = "B"
        elif income_symmetry >= 0.75:
            symmetry_grade = "C"
        elif income_symmetry >= 0.65:
            symmetry_grade = "D"
        else:
            symmetry_grade = "F"

    # Overall grade (average of letter grades)
    grade_map = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0, "N/A": 2}
    grades = [volatility_grade, symmetry_grade]
    valid_grades = [g for g in grades if g != "N/A"]
    if valid_grades:
        avg_grade = sum(grade_map[g] for g in valid_grades) / len(valid_grades)
        if avg_grade >= 3.5:
            overall_grade = "A"
        elif avg_grade >= 2.5:
            overall_grade = "B"
        elif avg_grade >= 1.5:
            overall_grade = "C"
        elif avg_grade >= 0.5:
            overall_grade = "D"
        else:
            overall_grade = "F"
    else:
        overall_grade = "N/A"

    # Interpretation
    risk_factors = []
    if volatility_cv is not None and volatility_cv > 25:
        risk_factors.append("high unemployment volatility")
    if income_symmetry is not None and income_symmetry < 0.80:
        risk_factors.append("significant income inequality (median << average)")

    if not risk_factors:
        interpretation = "Low risk profile — stable employment and balanced income distribution"
    else:
        interpretation = f"Risk factors: {', '.join(risk_factors)}"

    return {
        "volatility_cv": volatility_cv,
        "volatility_grade": volatility_grade,
        "income_symmetry": income_symmetry,
        "symmetry_grade": symmetry_grade,
        "overall_grade": overall_grade,
        "interpretation": interpretation,
    }


# ── E. Education ROI ──────────────────────────────────────────────

# Estimated annual education costs in Canada (tuition + living, rough averages)
EDUCATION_COSTS = {
    "High school diploma": 0,
    "Apprenticeship/trades": 8_000,
    "College/CEGEP": 12_000,
    "Bachelor's degree": 22_000,
    "Master's degree": 25_000,
    "Earned doctorate": 28_000,
}

EDUCATION_DURATIONS = {
    "High school diploma": 0,
    "Apprenticeship/trades": 2,
    "College/CEGEP": 2,
    "Bachelor's degree": 4,
    "Master's degree": 2,
    "Earned doctorate": 4,
}


def compute_education_roi(page2_data: dict) -> dict:
    """Compute education ROI: income premium, marginal return, break-even years.

    Uses by_education data from income analysis to compare adjacent levels.
    Returns: {levels: [{from_level, to_level, income_premium, premium_pct,
              total_cost, break_even_years}], best_roi}
    """
    income = page2_data.get("income", {})
    by_education = income.get("by_education", [])

    if len(by_education) < 2:
        return {"error": "Insufficient education-level income data for ROI"}

    # Build ordered income map
    edu_order = [
        "High school diploma",
        "Apprenticeship/trades",
        "College/CEGEP",
        "Bachelor's degree",
        "Master's degree",
        "Earned doctorate",
    ]

    income_map = {}
    for entry in by_education:
        income_map[entry["education"]] = entry["median_income"]

    levels = []
    available = [e for e in edu_order if e in income_map]

    for i in range(1, len(available)):
        from_level = available[i - 1]
        to_level = available[i]
        from_income = income_map[from_level]
        to_income = income_map[to_level]

        income_premium = to_income - from_income
        premium_pct = round((income_premium / from_income * 100) if from_income > 0 else 0, 1)

        annual_cost = EDUCATION_COSTS.get(to_level, 20_000)
        duration = EDUCATION_DURATIONS.get(to_level, 2)
        total_cost = annual_cost * duration

        # Break-even: total_cost / annual_income_premium
        if income_premium > 0:
            break_even = round(total_cost / income_premium, 1)
        else:
            break_even = None  # No positive return

        levels.append({
            "from_level": from_level,
            "to_level": to_level,
            "from_income": from_income,
            "to_income": to_income,
            "income_premium": round(income_premium, 0),
            "premium_pct": premium_pct,
            "total_cost": total_cost,
            "duration_years": duration,
            "break_even_years": break_even,
        })

    # Best ROI = shortest break-even among positive premiums
    positive = [l for l in levels if l["break_even_years"] is not None and l["break_even_years"] > 0]
    best_roi = min(positive, key=lambda x: x["break_even_years"]) if positive else None

    return {
        "levels": levels,
        "best_roi": best_roi,
    }


# ── F. Field Competitiveness ──────────────────────────────────────


def compute_field_competitiveness(page2_data: dict) -> dict:
    """Rank user's field on employment rate + income among all fields.

    Returns: {employment_rank, income_rank, total_fields,
              emp_quartile, inc_quartile, strengths, weaknesses,
              field_rankings: [{field, employment_rate, median_income, combined_rank}]}
    """
    labour = page2_data.get("labour_force", {})
    income = page2_data.get("income", {})
    user_field = labour.get("user_field", "")

    comparison = labour.get("comparison", [])
    ranking = income.get("ranking", [])

    if not comparison and not ranking:
        return {"error": "Insufficient data for competitiveness analysis"}

    # Build combined field data
    emp_map = {c["field"]: c["employment_rate"] for c in comparison}
    inc_map = {r["field"]: r["median_income"] for r in ranking}

    all_fields = sorted(set(emp_map.keys()) | set(inc_map.keys()))
    total_fields = len(all_fields)

    # Rank by employment rate (descending — higher is better)
    emp_sorted = sorted(all_fields, key=lambda f: emp_map.get(f, 0), reverse=True)
    emp_rank_map = {f: i + 1 for i, f in enumerate(emp_sorted)}

    # Rank by income (descending — higher is better)
    inc_sorted = sorted(all_fields, key=lambda f: inc_map.get(f, 0), reverse=True)
    inc_rank_map = {f: i + 1 for i, f in enumerate(inc_sorted)}

    # Combined rankings
    field_rankings = []
    for f in all_fields:
        er = emp_rank_map.get(f, total_fields)
        ir = inc_rank_map.get(f, total_fields)
        field_rankings.append({
            "field": f,
            "employment_rate": emp_map.get(f),
            "median_income": inc_map.get(f),
            "emp_rank": er,
            "inc_rank": ir,
            "combined_rank": er + ir,
        })
    field_rankings.sort(key=lambda x: x["combined_rank"])

    # User's field
    user_emp_rank = None
    user_inc_rank = None
    for f in all_fields:
        if user_field in f or f in user_field:
            user_emp_rank = emp_rank_map.get(f)
            user_inc_rank = inc_rank_map.get(f)
            break

    # Quartile analysis
    q1_threshold = max(1, total_fields // 4)
    q4_threshold = total_fields - q1_threshold

    def quartile_label(rank):
        if rank is None:
            return "N/A"
        if rank <= q1_threshold:
            return "Top quartile"
        if rank <= total_fields // 2:
            return "Second quartile"
        if rank <= q4_threshold:
            return "Third quartile"
        return "Bottom quartile"

    emp_quartile = quartile_label(user_emp_rank)
    inc_quartile = quartile_label(user_inc_rank)

    # Strengths and weaknesses
    strengths = []
    weaknesses = []
    if user_emp_rank and user_emp_rank <= q1_threshold:
        strengths.append("High employment rate")
    if user_inc_rank and user_inc_rank <= q1_threshold:
        strengths.append("High income")
    if user_emp_rank and user_emp_rank > q4_threshold:
        weaknesses.append("Low employment rate")
    if user_inc_rank and user_inc_rank > q4_threshold:
        weaknesses.append("Low income relative to other fields")

    return {
        "employment_rank": user_emp_rank,
        "income_rank": user_inc_rank,
        "total_fields": total_fields,
        "emp_quartile": emp_quartile,
        "inc_quartile": inc_quartile,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "field_rankings": field_rankings,
    }


# ── G. Career Quadrant (Employability vs Income) ──────────────────


# Short display names for the 11 broad fields
_SHORT_NAMES = {
    "Education": "Education",
    "Visual and performing arts, and communications technologies": "Arts & Media",
    "Humanities": "Humanities",
    "Social and behavioural sciences and law": "Social Sci & Law",
    "Business, management and public administration": "Business",
    "Physical and life sciences and technologies": "Life Sciences",
    "Mathematics, computer and information sciences": "Math & CS",
    "Architecture, engineering, and related trades": "Engineering",
    "Agriculture, natural resources and conservation": "Agriculture",
    "Health and related fields": "Health",
    "Personal, protective and transportation services": "Services",
}


def compute_career_quadrant(page2_data: dict) -> dict:
    """Build data for a 4-quadrant scatter plot.

    X = employment rate (career possibility / employability)
    Y = median income   (career prospects / earning potential)

    Returns: {fields: [{field, short_name, employment_rate, median_income, is_user}],
              emp_midpoint, inc_midpoint, emp_min, emp_max, inc_min, inc_max,
              user_quadrant}
    """
    labour = page2_data.get("labour_force", {})
    income = page2_data.get("income", {})
    user_field = labour.get("user_field", "")

    comparison = labour.get("comparison", [])
    ranking = income.get("ranking", [])

    if not comparison or not ranking:
        return {"error": "Insufficient data for career quadrant analysis"}

    emp_map = {c["field"]: c["employment_rate"] for c in comparison}
    inc_map = {r["field"]: r["median_income"] for r in ranking}

    # Only include fields that have both employment rate and income data
    common_fields = sorted(set(emp_map.keys()) & set(inc_map.keys()))
    if len(common_fields) < 3:
        return {"error": "Too few fields with both employment and income data"}

    fields = []
    for f in common_fields:
        is_user = user_field in f or f in user_field
        fields.append({
            "field": f,
            "short_name": _SHORT_NAMES.get(f, f[:20]),
            "employment_rate": emp_map[f],
            "median_income": inc_map[f],
            "is_user": is_user,
        })

    all_emp = [f["employment_rate"] for f in fields]
    all_inc = [f["median_income"] for f in fields]

    emp_midpoint = float(np.median(all_emp))
    inc_midpoint = float(np.median(all_inc))

    # Determine user's quadrant
    user_entries = [f for f in fields if f["is_user"]]
    if user_entries:
        u = user_entries[0]
        high_emp = u["employment_rate"] >= emp_midpoint
        high_inc = u["median_income"] >= inc_midpoint
        if high_emp and high_inc:
            user_quadrant = "High Employability + High Income"
        elif not high_emp and high_inc:
            user_quadrant = "Competitive/Niche + High Income"
        elif high_emp and not high_inc:
            user_quadrant = "Accessible + Lower Income"
        else:
            user_quadrant = "Challenging + Lower Income"
    else:
        user_quadrant = "N/A"

    return {
        "fields": fields,
        "emp_midpoint": round(emp_midpoint, 1),
        "inc_midpoint": round(inc_midpoint, 0),
        "emp_min": round(min(all_emp) - 2, 1),
        "emp_max": round(max(all_emp) + 2, 1),
        "inc_min": round(min(all_inc) * 0.9, 0),
        "inc_max": round(max(all_inc) * 1.1, 0),
        "user_quadrant": user_quadrant,
    }


# ── H. Subfield Quadrant (within same broad field) ────────────────


def compute_subfield_quadrant(page2_data: dict) -> dict:
    """Build 4-quadrant scatter data for subfields within the user's broad field.

    X = employment rate, Y = median income.
    Subfields without their own employment data inherit from parent 2-digit CIP
    or the broad field average (marked as estimated).

    Returns: {fields, emp_midpoint, inc_midpoint, emp_min, emp_max,
              inc_min, inc_max, user_quadrant, broad_field, has_data}
    """
    sf_data = page2_data.get("subfield_comparison", {})
    subfields = sf_data.get("subfields", [])
    user_subfield = sf_data.get("user_subfield")
    broad_field = sf_data.get("broad_field", "")

    if len(subfields) < 2:
        return {"error": f"Insufficient subfield data for {broad_field} (need at least 2 subfields)"}

    # Build short display names: "11.07 Computer science" -> "Computer science"
    def short_name(name: str) -> str:
        # Strip CIP prefix like "11.07 " or "11. "
        parts = name.split(" ", 1)
        if len(parts) == 2 and parts[0].replace(".", "").isdigit():
            return parts[1]
        return name[:25]

    fields = []
    for sf in subfields:
        is_user = (user_subfield is not None and
                   (user_subfield == sf["name"] or
                    sf["name"] in user_subfield or
                    user_subfield in sf["name"]))
        fields.append({
            "field": sf["name"],
            "short_name": short_name(sf["name"]),
            "employment_rate": sf["employment_rate"],
            "median_income": sf["median_income"],
            "emp_exact": sf.get("emp_exact", True),
            "is_user": is_user,
        })

    all_emp = [f["employment_rate"] for f in fields]
    all_inc = [f["median_income"] for f in fields]

    emp_midpoint = float(np.median(all_emp))
    inc_midpoint = float(np.median(all_inc))

    # User's quadrant
    user_entries = [f for f in fields if f["is_user"]]
    if user_entries:
        u = user_entries[0]
        high_emp = u["employment_rate"] >= emp_midpoint
        high_inc = u["median_income"] >= inc_midpoint
        if high_emp and high_inc:
            user_quadrant = "High Employability + High Income"
        elif not high_emp and high_inc:
            user_quadrant = "Competitive/Niche + High Income"
        elif high_emp and not high_inc:
            user_quadrant = "Accessible + Lower Income"
        else:
            user_quadrant = "Challenging + Lower Income"
    else:
        user_quadrant = "N/A"

    return {
        "fields": fields,
        "emp_midpoint": round(emp_midpoint, 1),
        "inc_midpoint": round(inc_midpoint, 0),
        "emp_min": round(min(all_emp) - 2, 1),
        "emp_max": round(max(all_emp) + 2, 1),
        "inc_min": round(min(all_inc) * 0.9, 0),
        "inc_max": round(max(all_inc) * 1.1, 0),
        "user_quadrant": user_quadrant,
        "broad_field": broad_field,
        "has_estimated_emp": any(not f["emp_exact"] for f in fields),
    }


# ── Run All Analyses ──────────────────────────────────────────────


def run_all_analyses(page2_data: dict) -> dict:
    """Run all analysis modules. Returns dict keyed by analysis name."""
    return {
        "composite_score": compute_composite_score(page2_data),
        "unemployment_forecast": compute_unemployment_forecast(page2_data),
        "vacancy_forecast": compute_vacancy_forecast(page2_data),
        "income_projection": compute_income_projection(page2_data),
        "risk_assessment": compute_risk_assessment(page2_data),
        "education_roi": compute_education_roi(page2_data),
        "field_competitiveness": compute_field_competitiveness(page2_data),
        "career_quadrant": compute_career_quadrant(page2_data),
        "subfield_quadrant": compute_subfield_quadrant(page2_data),
    }
