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
    margin=dict(l=20, r=20, t=60, b=20),
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
            font=dict(size=16, family="Inter, sans-serif", color="#1E293B"),
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
