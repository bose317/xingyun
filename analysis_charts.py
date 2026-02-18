"""Plotly chart functions for Page 3 deep analysis.

Reuses LAYOUT_DEFAULTS and color patterns from charts.py.
"""

import plotly.graph_objects as go

from charts import HIGHLIGHT_COLOR, USER_COLOR, DEFAULT_COLOR, SECONDARY_COLOR, LAYOUT_DEFAULTS, _apply_layout, _empty_chart


# ── 1. Composite Score Gauge ──────────────────────────────────────


def composite_score_gauge(score_data: dict) -> go.Figure:
    """Gauge chart for composite career prospect score (0-100)."""
    total = score_data.get("total", 0)
    grade = score_data.get("grade", "?")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        title={"text": f"Grade: {grade}", "font": {"size": 22, "family": "Inter, sans-serif", "color": "#1E293B"}},
        number={"suffix": "/100", "font": {"size": 42, "family": "Inter, sans-serif", "color": "#1E293B"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 2, "tickcolor": "#CBD5E1"},
            "bar": {"color": HIGHLIGHT_COLOR, "thickness": 0.75},
            "bgcolor": "#F1F5F9",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 35], "color": "#FEE2E2"},
                {"range": [35, 50], "color": "#FEF3C7"},
                {"range": [50, 65], "color": "#FEF9C3"},
                {"range": [65, 80], "color": "#D1FAE5"},
                {"range": [80, 100], "color": "#A7F3D0"},
            ],
            "threshold": {
                "line": {"color": "#1E293B", "width": 3},
                "thickness": 0.85,
                "value": total,
            },
        },
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=350)
    return fig


# ── 2. Component Radar Chart ─────────────────────────────────────


def component_radar(score_data: dict) -> go.Figure:
    """5-axis radar for composite score sub-components."""
    components = score_data.get("components", {})
    if not components:
        return _empty_chart("No component data available")

    categories = list(components.keys())
    values = list(components.values())
    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.12)",
        line=dict(color=HIGHLIGHT_COLOR, width=2.5),
        marker=dict(size=8, color=HIGHLIGHT_COLOR, line=dict(width=2, color="white")),
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(148,163,184,0.2)"),
            angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
        ),
    )
    return _apply_layout(fig, "Score Components", height=400)


# ── 3. Unemployment Forecast Line Chart ──────────────────────────


def unemployment_forecast_chart(forecast: dict) -> go.Figure:
    """Line chart with historical data, smoothed trend, and 3-year forecast."""
    if "error" in forecast:
        return _empty_chart(forecast["error"])

    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=forecast["dates"], y=forecast["values"],
        mode="lines+markers", name="Historical",
        line=dict(color="#94A3B8", width=1.5, dash="dot", shape="spline"),
        marker=dict(size=4, color="#94A3B8"),
        hovertemplate="Year: %{x}<br>Rate: %{y:.1f}%<extra></extra>",
    ))

    # Smoothed
    fig.add_trace(go.Scatter(
        x=forecast["dates"], y=forecast["smoothed"],
        mode="lines", name="Smoothed (3yr MA)",
        line=dict(color=DEFAULT_COLOR, width=2.5, shape="spline"),
        hovertemplate="Year: %{x}<br>Smoothed: %{y:.1f}%<extra></extra>",
    ))

    # Confidence band (drawn before forecast so it's behind)
    fig.add_trace(go.Scatter(
        x=forecast["forecast_dates"] + forecast["forecast_dates"][::-1],
        y=forecast["upper_band"] + forecast["lower_band"][::-1],
        fill="toself", fillcolor="rgba(99, 102, 241, 0.1)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=True, name="Confidence Band",
        hoverinfo="skip",
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast["forecast_dates"], y=forecast["forecast_values"],
        mode="lines+markers", name="Forecast",
        line=dict(color=HIGHLIGHT_COLOR, width=3, dash="dash"),
        marker=dict(size=10, color=HIGHLIGHT_COLOR, line=dict(width=2, color="white")),
        hovertemplate="Year: %{x}<br>Forecast: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        yaxis_title="Unemployment Rate (%)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return _apply_layout(fig, "Unemployment Rate Forecast", height=450)


# ── 4. Vacancy Forecast Line Chart ───────────────────────────────


def vacancy_forecast_chart(forecast: dict) -> go.Figure:
    """Line chart with historical vacancy data and forecast."""
    if "error" in forecast:
        return _empty_chart(forecast["error"])

    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=forecast["dates"], y=forecast["values"],
        mode="lines+markers", name="Historical",
        line=dict(color="#94A3B8", width=1.5, dash="dot", shape="spline"),
        marker=dict(size=4, color="#94A3B8"),
        hovertemplate="Date: %{x}<br>Vacancies: %{y:,.0f}<extra></extra>",
    ))

    # Smoothed
    fig.add_trace(go.Scatter(
        x=forecast["dates"], y=forecast["smoothed"],
        mode="lines", name="Smoothed (3Q MA)",
        line=dict(color=DEFAULT_COLOR, width=2.5, shape="spline"),
        hovertemplate="Date: %{x}<br>Smoothed: %{y:,.0f}<extra></extra>",
    ))

    # Confidence band
    fig.add_trace(go.Scatter(
        x=forecast["forecast_dates"] + forecast["forecast_dates"][::-1],
        y=forecast["upper_band"] + forecast["lower_band"][::-1],
        fill="toself", fillcolor="rgba(139, 92, 246, 0.1)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=True, name="Confidence Band",
        hoverinfo="skip",
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast["forecast_dates"], y=forecast["forecast_values"],
        mode="lines+markers", name="Forecast",
        line=dict(color=SECONDARY_COLOR, width=3, dash="dash"),
        marker=dict(size=10, color=SECONDARY_COLOR, line=dict(width=2, color="white")),
        hovertemplate="Period: %{x}<br>Forecast: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        yaxis_title="Job Vacancies",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return _apply_layout(fig, "Job Vacancy Forecast", height=450)


# ── 5. Income Projection Curve ───────────────────────────────────


def income_projection_chart(projection: dict) -> go.Figure:
    """Logarithmic income projection curve with data points and projections."""
    if "error" in projection:
        return _empty_chart(projection["error"])

    fig = go.Figure()

    # Fitted curve
    fig.add_trace(go.Scatter(
        x=projection["curve_years"], y=projection["curve_incomes"],
        mode="lines", name="Projected Curve",
        line=dict(color=DEFAULT_COLOR, width=2),
        hovertemplate="Year %{x}<br>Income: $%{y:,.0f}<extra></extra>",
    ))

    # Actual data points
    dp = projection["data_points"]
    fig.add_trace(go.Scatter(
        x=[p["year"] for p in dp], y=[p["income"] for p in dp],
        mode="markers+text", name="Actual Data",
        marker=dict(size=14, color=USER_COLOR, symbol="circle"),
        text=[f"${p['income']:,.0f}" for p in dp],
        textposition="top center",
        hovertemplate="Year %{x}<br>Actual: $%{y:,.0f}<extra></extra>",
    ))

    # Projected points
    pp = projection["projected_points"]
    fig.add_trace(go.Scatter(
        x=[p["year"] for p in pp], y=[p["income"] for p in pp],
        mode="markers+text", name="Projected",
        marker=dict(size=14, color=SECONDARY_COLOR, symbol="diamond"),
        text=[f"${p['income']:,.0f}" for p in pp],
        textposition="top center",
        hovertemplate="Year %{x}<br>Projected: $%{y:,.0f}<extra></extra>",
    ))

    # Field average line
    if projection.get("field_avg_2yr"):
        fig.add_hline(
            y=projection["field_avg_2yr"],
            line_dash="dot", line_color="#999",
            annotation_text=f"Field Avg (2yr): ${projection['field_avg_2yr']:,.0f}",
            annotation_position="top left",
        )

    fig.update_layout(
        xaxis_title="Years After Graduation",
        yaxis_title="Median Income ($)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return _apply_layout(fig, "Income Growth Projection", height=450)


# ── 6. Risk Assessment Bars ──────────────────────────────────────


def risk_assessment_chart(risk: dict) -> go.Figure:
    """Bar chart showing risk metrics with color-coded grades."""
    if "error" in risk:
        return _empty_chart(risk["error"])

    grade_colors = {"A": "#10B981", "B": "#06B6D4", "C": "#F59E0B", "D": "#F97316", "F": "#EF4444", "N/A": "#94A3B8"}

    metrics = []
    values = []
    colors = []
    annotations = []

    if risk.get("volatility_cv") is not None:
        metrics.append("Unemployment<br>Volatility (CV%)")
        values.append(risk["volatility_cv"])
        colors.append(grade_colors.get(risk["volatility_grade"], "#9E9E9E"))
        annotations.append(f"Grade: {risk['volatility_grade']}")

    if risk.get("income_symmetry") is not None:
        metrics.append("Income<br>Symmetry Ratio")
        values.append(risk["income_symmetry"] * 100)  # Scale to percentage for visual
        colors.append(grade_colors.get(risk["symmetry_grade"], "#9E9E9E"))
        annotations.append(f"Grade: {risk['symmetry_grade']}")

    if not metrics:
        return _empty_chart("Insufficient data for risk assessment")

    fig = go.Figure(go.Bar(
        x=metrics, y=values,
        marker_color=colors,
        text=annotations,
        textposition="outside",
        hovertemplate="%{x}<br>Value: %{y:.1f}<extra></extra>",
    ))

    fig.update_layout(
        yaxis_title="Score",
        showlegend=False,
    )
    return _apply_layout(fig, f"Risk Assessment — Overall: {risk.get('overall_grade', 'N/A')}", height=400)


# ── 7. Education ROI Waterfall ───────────────────────────────────


def education_roi_waterfall(roi: dict) -> go.Figure:
    """Waterfall chart showing income premium at each education level."""
    if "error" in roi:
        return _empty_chart(roi["error"])

    levels = roi.get("levels", [])
    if not levels:
        return _empty_chart("No ROI data available")

    # Build waterfall data
    labels = [levels[0]["from_level"]]
    values = [levels[0]["from_income"]]
    measure = ["absolute"]

    for level in levels:
        labels.append(f"+{level['to_level']}")
        values.append(level["income_premium"])
        measure.append("relative")

    # Final total
    labels.append("Final Level")
    values.append(levels[-1]["to_income"])
    measure.append("total")

    colors = []
    for i, m in enumerate(measure):
        if m == "absolute":
            colors.append(DEFAULT_COLOR)
        elif m == "total":
            colors.append(HIGHLIGHT_COLOR)
        else:
            colors.append("#4CAF50" if values[i] > 0 else "#F44336")

    fig = go.Figure(go.Waterfall(
        x=labels, y=values,
        measure=measure,
        connector={"line": {"color": "#ccc"}},
        increasing={"marker": {"color": "#10B981"}},
        decreasing={"marker": {"color": "#EF4444"}},
        totals={"marker": {"color": HIGHLIGHT_COLOR}},
        text=[f"${v:+,.0f}" if m == "relative" else f"${v:,.0f}" for v, m in zip(values, measure)],
        textposition="outside",
        hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        yaxis_title="Median Income ($)",
        showlegend=False,
    )
    return _apply_layout(fig, "Income Premium by Education Level", height=450)


# ── 8. Break-Even Timeline ──────────────────────────────────────


def break_even_timeline(roi: dict) -> go.Figure:
    """Horizontal bar chart showing break-even years for each education step."""
    if "error" in roi:
        return _empty_chart(roi["error"])

    levels = roi.get("levels", [])
    if not levels:
        return _empty_chart("No break-even data available")

    labels = []
    be_years = []
    colors = []
    texts = []

    for level in levels:
        label = f"{level['from_level'][:20]} -> {level['to_level'][:20]}"
        labels.append(label)
        be = level.get("break_even_years")
        if be is not None and be > 0:
            be_years.append(be)
            # Color code: green < 3yr, yellow 3-6yr, orange 6-10yr, red > 10yr
            if be < 3:
                colors.append("#10B981")
            elif be < 6:
                colors.append("#F59E0B")
            elif be < 10:
                colors.append("#F97316")
            else:
                colors.append("#EF4444")
            texts.append(f"{be:.1f} yrs (cost: ${level['total_cost']:,.0f})")
        else:
            be_years.append(0)
            colors.append("#9E9E9E")
            texts.append("No positive return")

    fig = go.Figure(go.Bar(
        x=be_years, y=labels,
        orientation="h",
        marker_color=colors,
        text=texts,
        textposition="outside",
        hovertemplate="%{y}<br>Break-even: %{x:.1f} years<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Break-Even (Years)",
        showlegend=False,
    )
    return _apply_layout(fig, "Education Investment Break-Even", height=max(300, len(levels) * 80))


# ── 9. Career Quadrant Chart ────────────────────────────────────


def career_quadrant_chart(quadrant_data: dict) -> go.Figure:
    """Four-quadrant scatter: X = employment rate, Y = median income.

    Quadrants:
      Top-right:    High employability + High income  (Star fields)
      Top-left:     Low employability  + High income  (Competitive/niche)
      Bottom-right: High employability + Low income   (Accessible but limited)
      Bottom-left:  Low employability  + Low income   (Challenging)
    """
    if "error" in quadrant_data:
        return _empty_chart(quadrant_data["error"])

    fields = quadrant_data["fields"]
    user_field = quadrant_data.get("user_field", "")
    emp_mid = quadrant_data["emp_midpoint"]
    inc_mid = quadrant_data["inc_midpoint"]

    fig = go.Figure()

    # Quadrant background shading
    # We'll use shapes for the 4 quadrant fills
    emp_min = quadrant_data.get("emp_min", emp_mid - 15)
    emp_max = quadrant_data.get("emp_max", emp_mid + 15)
    inc_min = quadrant_data.get("inc_min", inc_mid * 0.5)
    inc_max = quadrant_data.get("inc_max", inc_mid * 1.8)

    # Add faint quadrant backgrounds
    quadrant_colors = [
        # bottom-left
        (emp_min, emp_mid, inc_min, inc_mid, "rgba(239,68,68,0.06)"),
        # bottom-right
        (emp_mid, emp_max, inc_min, inc_mid, "rgba(245,158,11,0.06)"),
        # top-left
        (emp_min, emp_mid, inc_mid, inc_max, "rgba(139,92,246,0.06)"),
        # top-right
        (emp_mid, emp_max, inc_mid, inc_max, "rgba(16,185,129,0.06)"),
    ]
    for x0, x1, y0, y1, color in quadrant_colors:
        fig.add_shape(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            fillcolor=color, line=dict(width=0), layer="below",
        )

    # Quadrant labels
    label_font = dict(size=11, color="rgba(0,0,0,0.25)")
    fig.add_annotation(x=emp_mid + (emp_max - emp_mid) * 0.5, y=inc_max * 0.97,
                       text="High Employability<br>High Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="top")
    fig.add_annotation(x=emp_min + (emp_mid - emp_min) * 0.5, y=inc_max * 0.97,
                       text="Competitive/Niche<br>High Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="top")
    fig.add_annotation(x=emp_mid + (emp_max - emp_mid) * 0.5, y=inc_min + (inc_mid - inc_min) * 0.08,
                       text="Accessible<br>Lower Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="bottom")
    fig.add_annotation(x=emp_min + (emp_mid - emp_min) * 0.5, y=inc_min + (inc_mid - inc_min) * 0.08,
                       text="Challenging<br>Lower Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="bottom")

    # Midpoint reference lines
    fig.add_hline(y=inc_mid, line_dash="dash", line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=emp_mid, line_dash="dash", line_color="rgba(0,0,0,0.2)", line_width=1)

    # Other fields (non-user)
    other = [f for f in fields if not f["is_user"]]
    if other:
        fig.add_trace(go.Scatter(
            x=[f["employment_rate"] for f in other],
            y=[f["median_income"] for f in other],
            mode="markers+text",
            marker=dict(size=12, color=DEFAULT_COLOR, opacity=0.7,
                        line=dict(width=1, color="white")),
            text=[f["short_name"] for f in other],
            textposition="top center",
            textfont=dict(size=9, color="#555"),
            name="Other Fields",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Employment: %{x:.1f}%<br>"
                "Income: $%{y:,.0f}<extra></extra>"
            ),
        ))

    # User's field (highlighted, larger)
    user = [f for f in fields if f["is_user"]]
    if user:
        fig.add_trace(go.Scatter(
            x=[f["employment_rate"] for f in user],
            y=[f["median_income"] for f in user],
            mode="markers+text",
            marker=dict(size=20, color=USER_COLOR,
                        line=dict(width=2, color="white"),
                        symbol="star"),
            text=[f["short_name"] for f in user],
            textposition="bottom center",
            textfont=dict(size=11, color=USER_COLOR, family="Source Sans Pro,sans-serif"),
            name="Your Field",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Employment: %{x:.1f}%<br>"
                "Income: $%{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Employment Rate (%)",
        yaxis_title="Median Income ($)",
        xaxis=dict(range=[emp_min - 1, emp_max + 1]),
        yaxis=dict(range=[inc_min * 0.95, inc_max * 1.05]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
    )
    return _apply_layout(fig, "Career Quadrant — Employability vs Income", height=550)


# ── 10. Subfield Quadrant Chart ──────────────────────────────────


def subfield_quadrant_chart(quadrant_data: dict) -> go.Figure:
    """Four-quadrant scatter for subfields within the same broad field.

    Same axes as career_quadrant_chart but comparing CIP subfields.
    Subfields with estimated employment rates use a different marker.
    """
    if "error" in quadrant_data:
        return _empty_chart(quadrant_data["error"])

    fields = quadrant_data["fields"]
    broad_field = quadrant_data.get("broad_field", "")
    emp_mid = quadrant_data["emp_midpoint"]
    inc_mid = quadrant_data["inc_midpoint"]
    emp_min = quadrant_data.get("emp_min", emp_mid - 15)
    emp_max = quadrant_data.get("emp_max", emp_mid + 15)
    inc_min = quadrant_data.get("inc_min", inc_mid * 0.5)
    inc_max = quadrant_data.get("inc_max", inc_mid * 1.8)

    fig = go.Figure()

    # Quadrant backgrounds
    quadrant_colors = [
        (emp_min, emp_mid, inc_min, inc_mid, "rgba(244,67,54,0.06)"),
        (emp_mid, emp_max, inc_min, inc_mid, "rgba(255,193,7,0.06)"),
        (emp_min, emp_mid, inc_mid, inc_max, "rgba(255,152,0,0.06)"),
        (emp_mid, emp_max, inc_mid, inc_max, "rgba(76,175,80,0.06)"),
    ]
    for x0, x1, y0, y1, color in quadrant_colors:
        fig.add_shape(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            fillcolor=color, line=dict(width=0), layer="below",
        )

    # Quadrant labels
    label_font = dict(size=11, color="rgba(0,0,0,0.25)")
    fig.add_annotation(x=emp_mid + (emp_max - emp_mid) * 0.5, y=inc_max * 0.97,
                       text="High Employability<br>High Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="top")
    fig.add_annotation(x=emp_min + (emp_mid - emp_min) * 0.5, y=inc_max * 0.97,
                       text="Competitive/Niche<br>High Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="top")
    fig.add_annotation(x=emp_mid + (emp_max - emp_mid) * 0.5, y=inc_min + (inc_mid - inc_min) * 0.08,
                       text="Accessible<br>Lower Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="bottom")
    fig.add_annotation(x=emp_min + (emp_mid - emp_min) * 0.5, y=inc_min + (inc_mid - inc_min) * 0.08,
                       text="Challenging<br>Lower Income", showarrow=False,
                       font=label_font, xanchor="center", yanchor="bottom")

    # Midpoint lines
    fig.add_hline(y=inc_mid, line_dash="dash", line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=emp_mid, line_dash="dash", line_color="rgba(0,0,0,0.2)", line_width=1)

    # Non-user subfields: split by exact vs estimated employment
    other_exact = [f for f in fields if not f["is_user"] and f.get("emp_exact", True)]
    other_est = [f for f in fields if not f["is_user"] and not f.get("emp_exact", True)]

    if other_exact:
        fig.add_trace(go.Scatter(
            x=[f["employment_rate"] for f in other_exact],
            y=[f["median_income"] for f in other_exact],
            mode="markers+text",
            marker=dict(size=12, color=DEFAULT_COLOR, opacity=0.8,
                        line=dict(width=1, color="white")),
            text=[f["short_name"] for f in other_exact],
            textposition="top center",
            textfont=dict(size=9, color="#555"),
            name="Subfields",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Employment: %{x:.1f}%<br>"
                "Income: $%{y:,.0f}<extra></extra>"
            ),
        ))

    if other_est:
        fig.add_trace(go.Scatter(
            x=[f["employment_rate"] for f in other_est],
            y=[f["median_income"] for f in other_est],
            mode="markers+text",
            marker=dict(size=11, color=SECONDARY_COLOR, opacity=0.6,
                        symbol="diamond",
                        line=dict(width=1, color="white")),
            text=[f["short_name"] for f in other_est],
            textposition="top center",
            textfont=dict(size=9, color="#888"),
            name="Subfields (est. emp.)",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Employment: %{x:.1f}% (estimated)<br>"
                "Income: $%{y:,.0f}<extra></extra>"
            ),
        ))

    # User's subfield
    user = [f for f in fields if f["is_user"]]
    if user:
        fig.add_trace(go.Scatter(
            x=[f["employment_rate"] for f in user],
            y=[f["median_income"] for f in user],
            mode="markers+text",
            marker=dict(size=20, color=USER_COLOR,
                        line=dict(width=2, color="white"),
                        symbol="star"),
            text=[f["short_name"] for f in user],
            textposition="bottom center",
            textfont=dict(size=11, color=USER_COLOR,
                          family="Source Sans Pro,sans-serif"),
            name="Your Subfield",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Employment: %{x:.1f}%<br>"
                "Income: $%{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Employment Rate (%)",
        yaxis_title="Median Income ($)",
        xaxis=dict(range=[emp_min - 1, emp_max + 1]),
        yaxis=dict(range=[inc_min * 0.95, inc_max * 1.05]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
    )

    # Shorter broad field name for title
    short_broad = broad_field[:40] + "..." if len(broad_field) > 40 else broad_field
    return _apply_layout(fig, f"Within-Field Quadrant — {short_broad}", height=550)
