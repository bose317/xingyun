"""Plotly chart creation functions for employment prediction app."""

import plotly.graph_objects as go


# Modern color palette
HIGHLIGHT_COLOR = "#6366F1"   # Indigo  — chart accents (gauge, forecasts, radars)
USER_COLOR = "#EF4444"        # Red     — user's own field/major highlight
DEFAULT_COLOR = "#3B82F6"     # Blue    — other fields / general data
SECONDARY_COLOR = "#8B5CF6"   # Violet  — secondary series
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_ROSE = "#F43F5E"

# Gradient-like multi-series palette
SERIES_COLORS = [
    "#6366F1", "#3B82F6", "#06B6D4", "#10B981",
    "#F59E0B", "#F97316", "#EF4444", "#EC4899",
    "#8B5CF6", "#14B8A6", "#84CC16", "#F43F5E",
]

LAYOUT_DEFAULTS = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=12, family="Inter, -apple-system, sans-serif", color="#334155"),
    margin=dict(l=40, r=40, t=60, b=30),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#E2E8F0",
        font=dict(size=13, family="Inter, sans-serif", color="#1E293B"),
    ),
)

# Plotly animation config for smooth transitions
ANIMATION_CONFIG = dict(
    displayModeBar=False,
    scrollZoom=False,
)


def _apply_layout(fig: go.Figure, title: str = "", height: int = 500) -> go.Figure:
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(
            text=title,
            font=dict(size=17, family="Inter, sans-serif", color="#1E293B", weight=600),
            x=0.0,
            xanchor="left",
        ),
        height=height,
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="rgba(148,163,184,0.15)",
        zeroline=False,
        tickfont=dict(size=11, color="#64748B"),
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="rgba(148,163,184,0.15)",
        zeroline=False,
        tickfont=dict(size=11, color="#64748B"),
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=16, color="gray"))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False),
                      **LAYOUT_DEFAULTS, height=300)
    return fig


def employment_rate_bar(comparison: list[dict], user_field: str) -> go.Figure:
    """Horizontal bar chart: employment rate across fields, user's highlighted."""
    if not comparison:
        return _empty_chart("No employment rate data available")

    fields = [d["field"] for d in comparison]
    rates = [d["employment_rate"] for d in comparison]
    colors = [USER_COLOR if user_field in f else DEFAULT_COLOR for f in fields]
    labels = [f[:50] + "..." if len(f) > 50 else f for f in fields]

    fig = go.Figure(go.Bar(
        x=rates, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        text=[f"{r:.1f}%" for r in rates], textposition="outside",
        hovertemplate="%{y}<br>Employment Rate: %{x:.1f}%<extra></extra>",
    ))
    return _apply_layout(fig, "Employment Rate by Field of Study", height=max(400, len(fields) * 35))


def education_comparison_grouped(summary: dict, education: str) -> go.Figure:
    """Grouped bar chart: employment/participation/unemployment rates."""
    metrics = [
        ("Employment Rate", summary.get("employment_rate", 0), ACCENT_GREEN),
        ("Participation Rate", summary.get("participation_rate", 0), DEFAULT_COLOR),
        ("Unemployment Rate", summary.get("unemployment_rate", 0), ACCENT_ROSE),
    ]

    fig = go.Figure()
    for label, value, color in metrics:
        fig.add_trace(go.Bar(
            x=[label], y=[value], name=label, marker_color=color,
            text=[f"{value:.1f}%"], textposition="outside",
        ))
    fig.update_layout(showlegend=False, barmode="group")
    return _apply_layout(fig, f"Key Rates \u2014 {education}", height=400)


def income_ranking_bar(ranking: list[dict], user_field: str) -> go.Figure:
    """Horizontal bar chart of median income by field."""
    if not ranking:
        return _empty_chart("No income ranking data available")

    fields = [d["field"] for d in ranking]
    incomes = [d["median_income"] for d in ranking]
    colors = [USER_COLOR if user_field in f else DEFAULT_COLOR for f in fields]
    labels = [f[:50] + "..." if len(f) > 50 else f for f in fields]

    fig = go.Figure(go.Bar(
        x=incomes, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        text=[f"${v:,.0f}" for v in incomes], textposition="outside",
        hovertemplate="%{y}<br>Median Income: $%{x:,.0f}<extra></extra>",
    ))
    return _apply_layout(fig, "Median Income Ranking by Field", height=max(400, len(fields) * 35))


def income_by_education_line(by_education: list[dict], field: str) -> go.Figure:
    """Line chart: income vs education level."""
    if not by_education:
        return _empty_chart("No income by education data available")

    edu_labels = [d["education"] for d in by_education]
    incomes = [d["median_income"] for d in by_education]

    fig = go.Figure(go.Scatter(
        x=edu_labels, y=incomes, mode="lines+markers",
        marker=dict(size=10, color=HIGHLIGHT_COLOR, line=dict(width=2, color="white")),
        line=dict(color=HIGHLIGHT_COLOR, width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.08)",
        hovertemplate="%{x}<br>Median Income: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickangle=45)
    return _apply_layout(fig, f"Income by Education \u2014 {field}", height=450)


def unemployment_trend_lines(trends: dict, user_education: str) -> go.Figure:
    """Multi-line time series of unemployment rate by education level."""
    if not trends:
        return _empty_chart("No unemployment trend data available")

    # Map user education to the matching UNEMP_EDU key
    from config import EDUCATION_OPTIONS, UNEMP_EDU
    user_edu_id = EDUCATION_OPTIONS.get(user_education, {}).get("unemp")
    user_edu_name = None
    for ename, eid in UNEMP_EDU.items():
        if eid == user_edu_id:
            user_edu_name = ename
            break

    fig = go.Figure()
    color_idx = 0
    for edu_name, series in trends.items():
        dates = [d["date"] for d in series]
        values = [d["value"] for d in series]
        is_user = edu_name == user_edu_name
        c = USER_COLOR if is_user else SERIES_COLORS[color_idx % len(SERIES_COLORS)]
        color_idx += 1

        fig.add_trace(go.Scatter(
            x=dates, y=values, name=edu_name[:40], mode="lines",
            line=dict(width=3.5 if is_user else 1.5, color=c, shape="spline"),
            opacity=1.0 if is_user else 0.35,
            hovertemplate=f"{edu_name[:30]}<br>Year: %{{x}}<br>Rate: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font_size=10))
    return _apply_layout(fig, "Unemployment Rate Trends by Education Level", height=500)


def job_vacancy_dual_axis(trends: list[dict]) -> go.Figure:
    """Dual-axis chart: bars for vacancies, line for avg wage."""
    if not trends:
        return _empty_chart("No job vacancy data available")

    dates = [d["date"] for d in trends]
    vacancies = [d.get("vacancies") for d in trends]
    wages = [d.get("avg_wage") for d in trends]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=vacancies, name="Job Vacancies", marker_color=DEFAULT_COLOR, opacity=0.7,
        hovertemplate="Date: %{x}<br>Vacancies: %{y:,.0f}<extra></extra>",
    ))

    if any(w is not None for w in wages):
        fig.add_trace(go.Scatter(
            x=dates, y=wages, name="Avg Offered Wage", mode="lines+markers",
            marker=dict(size=6, color=HIGHLIGHT_COLOR),
            line=dict(color=HIGHLIGHT_COLOR, width=2), yaxis="y2",
            hovertemplate="Date: %{x}<br>Avg Wage: $%{y:,.2f}/hr<extra></extra>",
        ))
        fig.update_layout(yaxis2=dict(title="Avg Offered Wage ($/hr)", overlaying="y", side="right", showgrid=False))

    fig.update_layout(yaxis_title="Job Vacancies",
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    return _apply_layout(fig, "Job Vacancies & Offered Wages Over Time", height=450)


def graduate_income_trajectory(trajectory: list[dict]) -> go.Figure:
    """Connected dot chart: income at 2yr and 5yr post-graduation."""
    if not trajectory:
        return _empty_chart("No graduate outcome data available")

    years = [d["years_after"] for d in trajectory]
    incomes = [d["income"] for d in trajectory]

    fig = go.Figure(go.Scatter(
        x=years, y=incomes, mode="lines+markers+text",
        marker=dict(size=14, color=USER_COLOR, line=dict(width=2, color="white")),
        line=dict(color=USER_COLOR, width=3),
        text=[f"${v:,.0f}" for v in incomes], textposition="top center",
        hovertemplate="Years After Graduation: %{x}<br>Income: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(title="Years After Graduation",
                     tickvals=years, ticktext=[f"{y} years" for y in years])
    fig.update_yaxes(title="Median Income ($)")
    return _apply_layout(fig, "Income Growth After Graduation", height=400)


def cip_income_comparison_bar(broad_comparison: list[dict], user_broad_field: str) -> go.Figure:
    """Grouped bar chart: 2yr vs 5yr median income across all broad CIP fields."""
    if not broad_comparison:
        return _empty_chart("No CIP employment distribution data available")

    fields = [d["field"] for d in broad_comparison]
    labels = [f[:40] + "..." if len(f) > 40 else f for f in fields]
    income_2yr = [d.get("income_2yr", 0) for d in broad_comparison]
    income_5yr = [d.get("income_5yr", 0) for d in broad_comparison]

    # Highlight user's field
    colors_2yr = [
        "rgba(59, 130, 246, 0.9)" if user_broad_field not in f
        else "rgba(239, 68, 68, 0.9)"
        for f in fields
    ]
    colors_5yr = [
        "rgba(99, 102, 241, 0.9)" if user_broad_field not in f
        else "rgba(239, 68, 68, 0.6)"
        for f in fields
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=income_2yr, name="2 Years After Graduation",
        orientation="h",
        marker=dict(color=DEFAULT_COLOR, line=dict(width=0), cornerradius=3),
        text=[f"${v:,.0f}" for v in income_2yr], textposition="outside",
        hovertemplate="%{y}<br>2yr Income: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=income_5yr, name="5 Years After Graduation",
        orientation="h",
        marker=dict(color=HIGHLIGHT_COLOR, line=dict(width=0), cornerradius=3),
        text=[f"${v:,.0f}" for v in income_5yr], textposition="outside",
        hovertemplate="%{y}<br>5yr Income: $%{x:,.0f}<extra></extra>",
    ))

    # Mark user's field with annotation
    for i, f in enumerate(fields):
        if user_broad_field in f:
            fig.add_annotation(
                y=labels[i], x=max(income_5yr) * 1.15,
                text="Your Field", showarrow=False,
                font=dict(size=12, color=USER_COLOR, family="Inter, sans-serif"),
                xanchor="left",
            )

    fig.update_layout(
        barmode="group",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.15,
            xanchor="center", x=0.5, font_size=12,
        ),
        xaxis_title="Median Employment Income ($)",
    )
    return _apply_layout(
        fig,
        "Median Income by Field of Study — 2yr vs 5yr After Graduation",
        height=max(500, len(fields) * 55),
    )


def cip_subfield_income_bar(subfield_comparison: list[dict], user_field_name: str) -> go.Figure:
    """Grouped bar chart: 2yr vs 5yr income for sub-fields within a broad field."""
    if not subfield_comparison:
        return _empty_chart("No sub-field data available for this category")

    fields = [d["field"] for d in subfield_comparison]
    labels = [f[:40] + "..." if len(f) > 40 else f for f in fields]
    income_2yr = [d.get("income_2yr", 0) for d in subfield_comparison]
    income_5yr = [d.get("income_5yr", 0) for d in subfield_comparison]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=income_2yr, name="2 Years After",
        orientation="h",
        marker=dict(color=ACCENT_GREEN, line=dict(width=0), cornerradius=3),
        text=[f"${v:,.0f}" for v in income_2yr], textposition="outside",
        hovertemplate="%{y}<br>2yr Income: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=income_5yr, name="5 Years After",
        orientation="h",
        marker=dict(color=SECONDARY_COLOR, line=dict(width=0), cornerradius=3),
        text=[f"${v:,.0f}" for v in income_5yr], textposition="outside",
        hovertemplate="%{y}<br>5yr Income: $%{x:,.0f}<extra></extra>",
    ))

    # Highlight user's field
    for i, f in enumerate(fields):
        if user_field_name in f:
            fig.add_annotation(
                y=labels[i], x=max(income_5yr) * 1.15 if income_5yr else 0,
                text="You", showarrow=False,
                font=dict(size=12, color=USER_COLOR, family="Inter, sans-serif"),
                xanchor="left",
            )

    fig.update_layout(
        barmode="group",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.15,
            xanchor="center", x=0.5, font_size=12,
        ),
        xaxis_title="Median Employment Income ($)",
    )
    return _apply_layout(
        fig,
        "Sub-field Income Comparison — 2yr vs 5yr After Graduation",
        height=max(400, len(fields) * 55),
    )


def noc_distribution_donut(broad_distribution: list[dict]) -> go.Figure:
    """Donut chart showing NOC broad category distribution for a CIP field."""
    if not broad_distribution:
        return _empty_chart("No occupation distribution data available")

    labels = [d["noc"] for d in broad_distribution]
    values = [d["percentage"] for d in broad_distribution]
    counts = [d.get("count") for d in broad_distribution]

    # Shorten labels for the chart
    short_labels = []
    for label in labels:
        # Remove the leading digit and space (e.g., "2 Natural and applied sciences" → "Natural and applied sciences")
        parts = label.split(" ", 1)
        short_labels.append(parts[1] if len(parts) > 1 else label)

    hover_texts = []
    for i, label in enumerate(labels):
        cnt = f"<br>Count: {counts[i]:,}" if counts[i] else ""
        hover_texts.append(f"{label}<br>Proportion: {values[i]:.1f}%{cnt}")

    # Extract 1-digit NOC codes (e.g. "2 Natural and applied sciences" → "2")
    digit_codes = []
    for label in labels:
        parts = label.split(" ", 1)
        digit_codes.append(parts[0] if parts[0].isdigit() else label[:1])

    fig = go.Figure(go.Pie(
        labels=short_labels,
        values=values,
        hole=0.5,
        marker=dict(
            colors=SERIES_COLORS[:len(labels)],
            line=dict(color="white", width=2),
        ),
        text=digit_codes,
        textinfo="text",
        textposition="outside",
        textfont=dict(size=14, family="Inter, sans-serif", color="#334155"),
        hovertext=hover_texts,
        hoverinfo="text",
        sort=False,
    ))
    fig.update_layout(
        showlegend=False,
    )
    return _apply_layout(fig, "Occupation Distribution (NOC Broad Categories)", height=450)


def noc_distribution_bar(broad_distribution: list[dict]) -> go.Figure:
    """Horizontal bar chart showing NOC category proportions."""
    if not broad_distribution:
        return _empty_chart("No occupation distribution data available")

    raw_labels = [d["noc"] for d in broad_distribution]
    labels = [l[:40] + "..." if len(l) > 40 else l for l in raw_labels]
    values = [d["percentage"] for d in broad_distribution]
    colors = SERIES_COLORS[:len(labels)]

    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
        hovertemplate="%{y}<br>Proportion: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Proportion (%)")
    return _apply_layout(fig, "Employment Direction — Proportion by NOC Category", height=max(400, len(labels) * 40))


def noc_submajor_bar(submajor_distribution: list[dict], top_n: int = 15) -> go.Figure:
    """Horizontal bar chart showing top NOC sub-major group proportions."""
    if not submajor_distribution:
        return _empty_chart("No detailed occupation data available")

    data = submajor_distribution[:top_n]
    data = list(reversed(data))  # Reverse for horizontal bar (highest at top)

    raw_labels = [d["noc"] for d in data]
    labels = [l[:50] + "..." if len(l) > 50 else l for l in raw_labels]
    values = [d["percentage"] for d in data]
    counts = [d.get("count") for d in data]

    hover_texts = []
    for i in range(len(raw_labels)):
        cnt = f"<br>Count: {counts[i]:,}" if counts[i] else ""
        hover_texts.append(f"{raw_labels[i]}<br>Proportion: {values[i]:.1f}%{cnt}")

    # Gradient colors from low to high
    max_val = max(values) if values else 1
    colors = [
        f"rgba(99, 102, 241, {0.3 + 0.7 * v / max_val})"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
        hovertext=hover_texts, hoverinfo="text",
    ))
    fig.update_layout(xaxis_title="Proportion (%)")
    return _apply_layout(
        fig,
        f"Top {min(top_n, len(submajor_distribution))} Specific Occupation Groups (NOC 2-digit)",
        height=max(450, len(data) * 40),
    )


def noc_detail_bar(detail_distribution: list[dict], top_n: int = 15, oasis_noc_set: set | None = None) -> go.Figure:
    """Horizontal bar chart showing top specific occupations (5-digit NOC).

    If oasis_noc_set is provided, matching bars are highlighted in amber.
    """
    if not detail_distribution:
        return _empty_chart("No detailed occupation data available")

    data = detail_distribution[:top_n]
    data = list(reversed(data))  # Reverse for horizontal bar (highest at top)

    raw_labels = [d["noc"] for d in data]
    labels = [l[:55] + "..." if len(l) > 55 else l for l in raw_labels]
    values = [d["percentage"] for d in data]
    counts = [d.get("count") for d in data]

    hover_texts = []
    for i in range(len(raw_labels)):
        cnt = f"<br>Count: {counts[i]:,}" if counts[i] else ""
        hover_texts.append(f"{raw_labels[i]}<br>Proportion: {values[i]:.1f}%{cnt}")

    # Check which NOCs match OaSIS interests
    oasis_noc_set = oasis_noc_set or set()

    def _is_oasis_match(noc_label: str) -> bool:
        code = noc_label.split(" ", 1)[0]
        return code in oasis_noc_set

    # Color gradient based on value; amber for OaSIS matches
    max_val = max(values) if values else 1
    colors = []
    line_widths = []
    line_colors = []
    display_labels = []
    for i, v in enumerate(values):
        if _is_oasis_match(raw_labels[i]):
            colors.append(ACCENT_AMBER)
            line_widths.append(2)
            line_colors.append("#B45309")
            display_labels.append(f"\u2605 {labels[i]}")
        else:
            colors.append(f"rgba(99, 102, 241, {0.25 + 0.75 * v / max_val})")
            line_widths.append(0)
            line_colors.append("rgba(0,0,0,0)")
            display_labels.append(labels[i])

    fig = go.Figure(go.Bar(
        y=display_labels, x=values, orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=line_widths, color=line_colors),
            cornerradius=4,
        ),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
        hovertext=hover_texts, hoverinfo="text",
    ))
    fig.update_layout(xaxis_title="Proportion (%)")

    # Add legend annotation if any OaSIS matches exist
    if any(_is_oasis_match(l) for l in raw_labels):
        fig.add_annotation(
            text="\u2605 = OaSIS Interest Match",
            xref="paper", yref="paper", x=1.0, y=1.05,
            showarrow=False,
            font=dict(size=12, color="#B45309", family="Inter, sans-serif"),
            xanchor="right",
        )

    return _apply_layout(
        fig,
        f"Top {min(top_n, len(detail_distribution))} Specific Occupations (5-digit NOC)",
        height=max(500, len(data) * 35),
    )


def cip_growth_bar(broad_comparison: list[dict], user_broad_field: str) -> go.Figure:
    """Horizontal bar chart showing income growth percentage (2yr→5yr) by field."""
    data = [d for d in broad_comparison if d.get("growth_pct") is not None]
    if not data:
        return _empty_chart("No income growth data available")

    data.sort(key=lambda x: x["growth_pct"])
    fields = [d["field"] for d in data]
    labels = [f[:40] + "..." if len(f) > 40 else f for f in fields]
    growth = [d["growth_pct"] for d in data]
    colors = [
        USER_COLOR if user_broad_field in f else ACCENT_GREEN
        for f in fields
    ]

    fig = go.Figure(go.Bar(
        y=labels, x=growth, orientation="h",
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        text=[f"{g:+.1f}%" for g in growth], textposition="outside",
        hovertemplate="%{y}<br>Income Growth (2yr→5yr): %{x:+.1f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Income Growth (%)")
    return _apply_layout(
        fig,
        "Income Growth Rate by Field (2yr → 5yr After Graduation)",
        height=max(400, len(fields) * 35),
    )


def noc_quadrant_bubble(
    quadrant_data: list[dict],
    oasis_noc_set: set | None = None,
    highlight_label: str | None = None,
) -> go.Figure:
    """Quadrant bubble chart: X=employment count, Y=income, bubble size=employment share.

    Each bubble represents a specific occupation (5-digit NOC).
    Quadrant lines are drawn at the median of X and Y values.
    If oasis_noc_set is provided, matching bubbles are highlighted.
    highlight_label overrides the legend text (default: "OaSIS Interest Match").
    """
    if not quadrant_data:
        return _empty_chart("No data available for quadrant chart")

    # Filter to entries with valid count and income
    valid = [d for d in quadrant_data if d.get("income") is not None and d.get("count") is not None and d["count"] > 0]
    if not valid:
        return _empty_chart("Insufficient data for quadrant chart")

    oasis_noc_set = oasis_noc_set or set()

    def _is_oasis(noc_name: str) -> bool:
        return noc_name.split(" ", 1)[0] in oasis_noc_set

    counts = [d["count"] for d in valid]
    incomes = [d["income"] for d in valid]
    percentages = [d["percentage"] for d in valid]
    names = [d["noc"] for d in valid]

    # Compute medians for quadrant lines
    sorted_cnt = sorted(counts)
    sorted_inc = sorted(incomes)
    median_cnt = sorted_cnt[len(sorted_cnt) // 2]
    median_inc = sorted_inc[len(sorted_inc) // 2]

    # Scale bubble sizes: map percentage to a reasonable marker range (10-55)
    min_pct = min(percentages)
    max_pct = max(percentages)
    pct_range = max_pct - min_pct if max_pct != min_pct else 1
    sizes = [
        10 + 45 * (p - min_pct) / pct_range
        for p in percentages
    ]

    # Color by quadrant
    def _quadrant_color(cnt, inc):
        if cnt >= median_cnt and inc >= median_inc:
            return ACCENT_GREEN       # Top-right: many people + high income
        elif cnt < median_cnt and inc >= median_inc:
            return HIGHLIGHT_COLOR     # Top-left: fewer people + high income
        elif cnt >= median_cnt and inc < median_inc:
            return ACCENT_AMBER        # Bottom-right: many people + lower income
        else:
            return ACCENT_ROSE         # Bottom-left: fewer people + lower income

    _hl_label = highlight_label or "OaSIS Interest Match"
    _use_star = highlight_label is None  # stars only for OaSIS mode
    _hl_color = "#0EA5E9" if highlight_label else USER_COLOR  # sky-blue vs red
    _hl_border = "#0369A1" if highlight_label else "#991B1B"

    def _make_hover(i):
        growth_str = f"{valid[i]['income_growth']:+.0f}%" if valid[i].get("income_growth") is not None else "N/A"
        young_str = f"${valid[i]['income_young']:,.0f}" if valid[i].get("income_young") else "N/A"
        tag = f"<br><b>{'\u2605 ' if _use_star else ''}{_hl_label}</b>" if _is_oasis(names[i]) else ""
        return (
            f"<b>{names[i]}</b><br>"
            f"Employment count: {counts[i]:,}<br>"
            f"Employment share: {percentages[i]:.1f}%<br>"
            f"Income (25-64): ${incomes[i]:,.0f}<br>"
            f"Income (15-24): {young_str}<br>"
            f"Income growth: {growth_str}"
            f"{tag}"
        )

    fig = go.Figure()

    # Determine bubble colors: highlighted matches → special color, others → quadrant color
    bubble_colors = []
    bubble_line_colors = []
    bubble_line_widths = []
    for i in range(len(valid)):
        if _is_oasis(names[i]):
            bubble_colors.append(_hl_color)
            bubble_line_colors.append(_hl_border)
            bubble_line_widths.append(2.5)
        else:
            bubble_colors.append(_quadrant_color(counts[i], incomes[i]))
            bubble_line_colors.append("white")
            bubble_line_widths.append(1.5)

    # All points as regular bubbles
    fig.add_trace(go.Scatter(
        x=counts,
        y=incomes,
        mode="markers",
        marker=dict(
            size=sizes,
            color=bubble_colors,
            opacity=0.75,
            line=dict(width=bubble_line_widths, color=bubble_line_colors),
        ),
        hovertext=[_make_hover(i) for i in range(len(valid))],
        hoverinfo="text",
        showlegend=False,
    ))

    # Overlay stars inside matched bubbles (OaSIS mode only)
    oasis_idx = [i for i in range(len(valid)) if _is_oasis(names[i])]
    if _use_star:
        for i in oasis_idx:
            fig.add_annotation(
                x=counts[i], y=incomes[i],
                text="\u2605",
                showarrow=False,
                font=dict(size=max(10, int(sizes[i] * 0.45)), color="white"),
                xanchor="center", yanchor="middle",
            )

    # Quadrant divider lines
    fig.add_hline(
        y=median_inc, line_dash="dash", line_color="rgba(100,116,139,0.4)",
        line_width=1.5,
        annotation_text=f"Median income: ${median_inc:,.0f}",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#64748B"),
    )
    fig.add_vline(
        x=median_cnt, line_dash="dash", line_color="rgba(100,116,139,0.4)",
        line_width=1.5,
        annotation_text=f"Median count: {median_cnt:,}",
        annotation_position="top right",
        annotation_font=dict(size=10, color="#64748B"),
    )

    # Quadrant labels — inset near the median crosshair
    quadrant_labels = [
        (1.0, 1.0, "Many + High Pay", ACCENT_GREEN, "left", "bottom"),
        (0.0, 1.0, "Few + High Pay", HIGHLIGHT_COLOR, "right", "bottom"),
        (1.0, 0.0, "Many + Lower Pay", ACCENT_AMBER, "left", "top"),
        (0.0, 0.0, "Few + Lower Pay", ACCENT_ROSE, "right", "top"),
    ]
    for qx, qy, qlabel, qcolor, xa, ya in quadrant_labels:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=qx, y=qy, text=qlabel, showarrow=False,
            font=dict(size=11, color=qcolor, family="Inter, sans-serif"),
            opacity=0.6, xanchor=xa, yanchor=ya,
            xshift=-8 if xa == "left" else 8,
            yshift=8 if ya == "bottom" else -8,
        )

    fig.update_layout(
        xaxis_title="Employment Count (number of people)",
        yaxis_title="Median Income — Age 25-64 ($)",
        showlegend=False,
    )

    # Add legend annotation if highlighted matches exist
    if oasis_idx:
        legend_prefix = "<b>\u2605</b> = " if _use_star else "\u25CF = "
        fig.add_annotation(
            text=f"{legend_prefix}{_hl_label}",
            xref="paper", yref="paper", x=1.0, y=1.05,
            showarrow=False,
            font=dict(size=12, color=_hl_color, family="Inter, sans-serif"),
            xanchor="right",
        )

    return _apply_layout(
        fig,
        "Occupation Quadrant — Employment Count vs Income (bubble = share %)",
        height=600,
    )


def radar_overview(employment_rate, income_percentile, low_unemployment, vacancy_score, income_growth) -> go.Figure:
    """5-axis radar chart for overall field assessment (all values 0-100)."""
    categories = ["Employment Rate", "Income Ranking", "Low Unemployment", "Job Demand", "Income Growth"]
    values = [employment_rate, income_percentile, low_unemployment, vacancy_score, income_growth]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed, theta=categories_closed, fill="toself",
        fillcolor="rgba(239, 68, 68, 0.12)",
        line=dict(color=USER_COLOR, width=2.5),
        marker=dict(size=7, color=USER_COLOR, line=dict(width=2, color="white")),
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
    ))
    fig.update_layout(polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(148,163,184,0.2)"),
        angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
    ))
    return _apply_layout(fig, "Overall Field Assessment", height=450)
