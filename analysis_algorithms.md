# Deep Career Analysis — Algorithm Documentation

This document describes the six analytical algorithms implemented in `analysis_engine.py` for Page 3 of the YF Career Exploration application.

---

## A. Composite Career Prospect Score (0–100)

### Purpose
Combine multiple career indicators into a single composite score for quick assessment.

### Sub-Scores (each 0–100)

| Component | Weight | Data Source | Method |
|-----------|--------|-------------|--------|
| Employment | 25% | `labour_force.comparison` | Percentile rank of user's employment rate among all 11 fields |
| Income | 25% | `income.ranking` | Percentile rank of user's median income among all fields |
| Trend | 20% | `unemployment.trends` | Linear regression slope on user's unemployment series; negative slope = improving |
| Demand | 15% | `job_vacancies.trends` | Compare recent-half vs older-half average vacancies; positive change = better |
| Growth | 15% | `graduate_outcomes.summary.growth_pct` | Graduate income growth 2yr→5yr, benchmarked: 0–50% maps to 0–100 |

### Percentile Score Formula
```
percentile = (count_of_values_below / (n - 1)) * 100
```
Where n = total number of fields in comparison.

### Trend Score Mapping
```
trend_score = clamp(50 - slope * 25, 0, 100)
```
- Slope of -2 → score 100 (strong improvement)
- Slope of 0 → score 50 (neutral)
- Slope of +2 → score 0 (worsening)

### Demand Score Mapping
```
change_pct = (recent_avg - older_avg) / older_avg * 100
demand_score = clamp(50 + change_pct, 0, 100)
```

### Grade Thresholds
| Score Range | Grade |
|-------------|-------|
| 80–100 | A |
| 65–79 | B |
| 50–64 | C |
| 35–49 | D |
| 0–34 | F |

---

## B. Trend Analysis & 3-Year Forecast

### Purpose
Extrapolate unemployment and job vacancy trends using linear regression.

### Unemployment Forecast

**Input:** Up to 36 annual data points from Table 14100020.

**Steps:**
1. Extract user's education-level unemployment time series
2. Apply 3-point moving average smoothing: `smoothed[i] = mean(values[max(0,i-2):i+1])`
3. Fit linear regression: `numpy.polyfit(x, smoothed, degree=1)` → slope, intercept
4. Compute residual standard deviation: `std(smoothed - fitted)`
5. Extrapolate 3 years: `forecast[t] = slope * t + intercept`
6. Confidence band: `forecast ± 1 * std_residual`

**Interpretation:**
- slope < -0.1: "Improving"
- slope > +0.1: "Worsening"
- else: "Stable"

### Job Vacancy Forecast

**Input:** Up to 20 quarterly data points from Table 14100443.

Same algorithm as unemployment, but:
- Forecasts 3 quarters ahead
- Interpretation thresholds: slope > 100 = "Growing", slope < -100 = "Declining"

---

## C. Income Growth Projection

### Purpose
Project long-term income trajectory using a logarithmic growth model.

### Model
```
income = a * ln(year) + b
```

**Fitting:** Two data points from graduate outcomes:
- (2, income_2yr) and (5, income_5yr)

```
a = (income_5yr - income_2yr) / (ln(5) - ln(2))
b = income_2yr - a * ln(2)
```

**Projections:** Year 10 and Year 15 after graduation.

### Rationale
Logarithmic growth reflects the empirical pattern of diminishing income returns over career tenure — rapid growth early on that gradually plateaus.

### Field Average Comparison
The average 2-year income across all fields is computed from `graduate_outcomes.comparison` for benchmarking.

---

## D. Career Stability / Risk Assessment

### Purpose
Assess employment stability and income distribution risk.

### Metrics

#### 1. Unemployment Volatility (Coefficient of Variation)
```
CV = (std(unemployment_series) / mean(unemployment_series)) * 100
```
Higher CV = more volatile = higher risk.

| CV (%) | Grade |
|--------|-------|
| < 10 | A |
| 10–19 | B |
| 20–29 | C |
| 30–39 | D |
| ≥ 40 | F |

#### 2. Income Symmetry Ratio
```
symmetry = median_income / average_income
```
- Ratio = 1.0: perfectly symmetric (no inequality)
- Ratio < 1.0: right-skewed (inequality — a few earn much more)

| Ratio | Grade |
|-------|-------|
| ≥ 0.95 | A |
| 0.85–0.94 | B |
| 0.75–0.84 | C |
| 0.65–0.74 | D |
| < 0.65 | F |

#### 3. Overall Grade
Average of component letter grades (A=4, B=3, C=2, D=1, F=0), mapped back to letter.

---

## E. Education ROI

### Purpose
Evaluate the return on investment for each education level transition.

### Inputs
- Median income by education level from Table 98100409
- Estimated Canadian education costs (tuition + living):

| Level | Annual Cost | Duration |
|-------|------------|----------|
| High school diploma | $0 | 0 yr |
| Apprenticeship/trades | $8,000 | 2 yr |
| College/CEGEP | $12,000 | 2 yr |
| Bachelor's degree | $22,000 | 4 yr |
| Master's degree | $25,000 | 2 yr |
| Earned doctorate | $28,000 | 4 yr |

### Calculations

**Income Premium:**
```
premium = income_at_higher_level - income_at_lower_level
premium_pct = (premium / income_at_lower_level) * 100
```

**Total Cost:**
```
total_cost = annual_cost * duration_years
```

**Break-Even Years:**
```
break_even = total_cost / annual_income_premium
```
Only defined when income premium > 0.

### Best ROI
The education transition with the shortest break-even period.

---

## F. Field Competitiveness

### Purpose
Rank the user's field of study against all other fields on employment and income dimensions.

### Method
1. Rank all fields by employment rate (descending) → employment_rank
2. Rank all fields by median income (descending) → income_rank
3. Combined rank = employment_rank + income_rank (lower = better)

### Quartile Analysis
Fields are divided into quartiles (top 25%, second 25%, etc.):
- **Strengths**: metrics in top quartile
- **Weaknesses**: metrics in bottom quartile

---

## G. Career Quadrant (Employability vs Income)

### Purpose
Visualize all fields on a 2D scatter plot with four meaningful quadrants, showing relative career positioning.

### Axes
- **X-axis (Employment Rate):** From `labour_force.comparison` — measures job availability / employability
- **Y-axis (Median Income):** From `income.ranking` — measures earning potential / career prospects

### Quadrant Division
The dividing lines use the **median** of all fields on each axis:
```
emp_midpoint = median(all employment rates)
inc_midpoint = median(all median incomes)
```

| Quadrant | Employment | Income | Interpretation |
|----------|-----------|--------|----------------|
| Top-right | Above median | Above median | Strong on both dimensions |
| Top-left | Below median | Above median | Competitive entry, rewarding earnings |
| Bottom-right | Above median | Below median | Accessible jobs, limited income |
| Bottom-left | Below median | Below median | Challenging career outlook |

### Data Requirements
Only fields with **both** employment rate and income data are plotted. Minimum 3 fields required.

### User Field Identification
The user's field is matched by substring containment against the broad field name and displayed as a highlighted star marker.

---

## H. Subfield Quadrant (Within-Field Comparison)

### Purpose
Compare subfields within the user's own broad field of study (same CIP 2-digit prefix) on a 4-quadrant scatter plot.

### Data Source
New API fetch in `fetch_subfield_comparison()`:
- Employment rate: from Table 98100445 (labour force), for subfields that have a `labour_force` member ID
- Median income: from Table 98100409 (income), for all subfields with an `income` member ID

### Employment Rate Inheritance
Many CIP subfields (4-digit or 6-digit) only have income data in Statistics Canada. For these:
1. First try: inherit from the parent 2-digit CIP series if it has employment data
2. Fallback: use the broad field's employment rate
3. These inherited values are marked `emp_exact: false` and displayed with diamond markers on the chart

### Quadrant Logic
Same as Algorithm G (Career Quadrant) but applied to subfields within one broad field:
- Dividing lines at the **median** employment rate and median income of the plotted subfields
- User's specific subfield is highlighted with a star marker

### Visual Distinction
| Marker | Meaning |
|--------|---------|
| Circle (solid) | Subfield with exact employment + income data |
| Diamond (lighter) | Subfield with income data + estimated employment rate |
| Star (orange) | User's subfield |

---

## Data Flow

```
Page 2 (6 API fetches) → st.session_state["page2_data"] → analysis_engine.run_all_analyses() → Page 3 (10 charts)
```

No additional API calls are made on Page 3 — all analysis uses cached Page 2 data.

---

## Limitations & Assumptions

1. **Linear trend extrapolation** assumes recent trends continue; structural economic changes are not modeled.
2. **Logarithmic income model** is fitted from only 2 data points (2yr and 5yr); accuracy decreases for distant projections (10yr, 15yr).
3. **Education costs** are rough Canadian national averages and vary significantly by province and institution.
4. **Break-even calculation** does not account for opportunity cost (foregone income during study), inflation, or time value of money.
5. **Confidence bands** use ±1 standard deviation of residuals, which provides approximately 68% coverage under normality assumptions.
6. **Field competitiveness** compares only the 11 broad fields available from Statistics Canada; subfield granularity is not available for all metrics.
