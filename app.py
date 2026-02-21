"""YF — Career Exploration Application.

Queries Statistics Canada WDS REST API directly (no CSV downloads)
to display employment statistics and job market prospects.

Multi-page wizard: Page 1 collects user profile & matches field of study,
Page 2 shows the analysis tabs, Page 3 provides deep career analysis.
"""

import traceback

import streamlit as st

# Clear any stale cached data from previous code versions
st.cache_data.clear()

from config import FIELD_OPTIONS, EDUCATION_OPTIONS, GEO_OPTIONS
from cip_codes import CIP_TO_BROAD, CIP_SERIES, CIP_SUBSERIES, CIP_CODES
from field_matcher import match_fields, resolve_subfield
from processors import (
    fetch_cip_employment_distribution,
    fetch_graduate_outcomes,
    fetch_income,
    fetch_job_vacancies,
    fetch_labour_force,
    fetch_noc_distribution,
    fetch_noc_income_for_quadrant,
    fetch_subfield_comparison,
    fetch_unemployment_trends,
)
from charts import (
    cip_growth_bar,
    cip_income_comparison_bar,
    cip_subfield_income_bar,
    education_comparison_grouped,
    employment_rate_bar,
    graduate_income_trajectory,
    income_by_education_line,
    income_ranking_bar,
    job_vacancy_dual_axis,
    noc_detail_bar,
    noc_distribution_donut,
    noc_distribution_bar,
    noc_quadrant_bubble,
    noc_submajor_bar,
    radar_overview,
    unemployment_trend_lines,
)
from oasis_client import fetch_oasis_matches, HOLLAND_CODES, HOLLAND_DESCRIPTIONS
from analysis_engine import run_all_analyses
from analysis_charts import (
    composite_score_gauge,
    component_radar,
    unemployment_forecast_chart,
    vacancy_forecast_chart,
    income_projection_chart,
    risk_assessment_chart,
    education_roi_waterfall,
    break_even_timeline,
    career_quadrant_chart,
    subfield_quadrant_chart,
)
from styles import GLOBAL_CSS

st.set_page_config(
    page_title="YF \u2014 Career Exploration",
    page_icon="\u2B50",
    layout="wide",
)

# Inject global modern styles
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── Page 1: User Profile & Field Matching ─────────────────────────


def render_profile_page():
    st.title("YF \u2014 Career Exploration")
    st.caption("Step 1: Tell us about yourself")

    # ── Personal info ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input(
            "Name",
            value=st.session_state.get("user_name", ""),
        )
    with col2:
        user_age = st.slider(
            "Age",
            min_value=16,
            max_value=70,
            value=st.session_state.get("user_age", 25),
        )

    col3, col4 = st.columns(2)
    with col3:
        gender_options = ["Male", "Female", "Other"]
        gender_idx = 0
        saved_gender = st.session_state.get("user_gender")
        if saved_gender in gender_options:
            gender_idx = gender_options.index(saved_gender)
        user_gender = st.selectbox("Gender", gender_options, index=gender_idx)
    with col4:
        edu_keys = list(EDUCATION_OPTIONS.keys())
        edu_idx = 0
        saved_edu = st.session_state.get("education")
        if saved_edu in edu_keys:
            edu_idx = edu_keys.index(saved_edu)
        education = st.selectbox("Education Level", edu_keys, index=edu_idx)

    geo_idx = 0
    saved_geo = st.session_state.get("geo")
    if saved_geo in GEO_OPTIONS:
        geo_idx = GEO_OPTIONS.index(saved_geo)
    geo = st.selectbox("Province / Territory", GEO_OPTIONS, index=geo_idx)

    st.divider()

    # ── Field of study search ─────────────────────────────────
    st.subheader("Field of Study")

    # If Browse was just used, clear the search box
    if st.session_state.pop("_clear_search", False):
        _query_default = ""
    else:
        _query_default = st.session_state.get("_field_query", "")

    query = st.text_input(
        "Search by keyword or CIP code (e.g. 'computer science', '14.08')",
        value=_query_default,
        key="field_query",
    )

    broad_field = st.session_state.get("broad_field")
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")

    if query:
        matches = match_fields(query, FIELD_OPTIONS)
        if matches:
            options = [m["display_name"] for m in matches]
            # Pre-select if user already chose one
            preselect = 0
            saved_display = st.session_state.get("_selected_display")
            if saved_display in options:
                preselect = options.index(saved_display)

            choice = st.radio(
                "Select your field:",
                options,
                index=preselect,
                key="field_radio",
            )
            selected = matches[options.index(choice)]
            broad_field = selected["broad_field"]
            subfield = selected["subfield"]
            cip_code = selected.get("cip_code")
            cip_name = selected.get("cip_name")

            # Show fallback info when CIP has no exact subfield data
            if cip_code and not subfield:
                st.caption(
                    f"CIP {cip_code} has no dedicated statistics — "
                    f"analysis will use the broad category: {broad_field}"
                )
            elif cip_code and subfield and not subfield.startswith(cip_code):
                st.caption(
                    f"CIP {cip_code} mapped to nearest available data: {subfield}"
                )
        else:
            st.warning("No matches found. Try a different keyword or browse below.")
            broad_field = None
            subfield = None
            cip_code = None
            cip_name = None

    # Fallback: browse all fields (3-level CIP hierarchy)
    with st.expander("Browse all fields"):
        # ── Level 1: Broad field ──
        broad_fields = list(FIELD_OPTIONS.keys())
        browse_idx = 0
        if broad_field in broad_fields:
            browse_idx = broad_fields.index(broad_field)
        browse_broad = st.selectbox(
            "Broad field",
            broad_fields,
            index=browse_idx,
            key="browse_broad",
        )

        # ── Level 2: CIP series (2-digit) that map to this broad field ──
        series_for_broad = sorted(
            code for code, bf in CIP_TO_BROAD.items() if bf == browse_broad
        )
        series_options = {
            code: f"{code}. {CIP_SERIES.get(code, code)}"
            for code in series_for_broad
            if code in CIP_SERIES
        }
        if series_options:
            series_labels = ["(All series)"] + list(series_options.values())
            series_choice = st.selectbox(
                "Series (2-digit CIP)",
                series_labels,
                key="browse_series",
            )
            chosen_series = None
            if series_choice != "(All series)":
                # reverse lookup code from label
                for code, label in series_options.items():
                    if label == series_choice:
                        chosen_series = code
                        break
        else:
            chosen_series = None

        # ── Level 3: Subseries (4-digit) under chosen series ──
        chosen_subseries = None
        if chosen_series:
            subs_for_series = sorted(
                (code, name)
                for code, name in CIP_SUBSERIES.items()
                if code.startswith(chosen_series + ".")
            )
            if subs_for_series:
                sub4_labels = ["(All subseries)"] + [
                    f"{code} {name}" for code, name in subs_for_series
                ]
                sub4_choice = st.selectbox(
                    "Subseries (4-digit CIP)",
                    sub4_labels,
                    key="browse_sub4",
                )
                if sub4_choice != "(All subseries)":
                    chosen_subseries = sub4_choice.split(" ", 1)[0]

        # ── Level 4: Class (6-digit) under chosen subseries ──
        chosen_class = None
        if chosen_subseries:
            classes_for_sub = sorted(
                (code, name)
                for code, name in CIP_CODES.items()
                if code.startswith(chosen_subseries)
            )
            if classes_for_sub:
                cls_labels = ["(All programs)"] + [
                    f"{code} {name}" for code, name in classes_for_sub
                ]
                cls_choice = st.selectbox(
                    "Program (6-digit CIP)",
                    cls_labels,
                    key="browse_cls6",
                )
                if cls_choice != "(All programs)":
                    chosen_class = cls_choice.split(" ", 1)[0]

        if st.button("Use this field", key="use_browse"):
            _bf = browse_broad
            _sf = None
            _cc = None
            _cn = None
            if chosen_class:
                _cc = chosen_class
                _cn = CIP_CODES.get(chosen_class, "")
                _sf, _bf = resolve_subfield(_cc, browse_broad, FIELD_OPTIONS)
            elif chosen_subseries:
                general_code = chosen_subseries + "00"
                if general_code in CIP_CODES:
                    _cc = general_code
                    _cn = CIP_CODES[general_code]
                else:
                    first = sorted(
                        c for c in CIP_CODES if c.startswith(chosen_subseries)
                    )
                    _cc = first[0] if first else None
                    _cn = CIP_CODES.get(_cc, "") if _cc else None
                if _cc:
                    _sf, _bf = resolve_subfield(_cc, browse_broad, FIELD_OPTIONS)
            # Persist immediately so values survive the next rerun
            st.session_state["broad_field"] = _bf
            st.session_state["subfield"] = _sf
            st.session_state["cip_code"] = _cc
            st.session_state["cip_name"] = _cn
            st.session_state["_field_query"] = ""
            st.session_state["_clear_search"] = True
            st.rerun()

    st.divider()

    # ── Interest Profile (OaSIS) ─────────────────────────────
    st.subheader("Interest Profile (OaSIS)")
    st.caption(
        "Select your top 3 Holland Code interests in order of dominance. "
        "This will be used to find matching occupations via the OaSIS Advanced Interest Search."
    )

    holland_names = list(HOLLAND_CODES.keys())

    saved_i1 = st.session_state.get("oasis_interest_1", holland_names[0])
    saved_i2 = st.session_state.get("oasis_interest_2", holland_names[1])
    saved_i3 = st.session_state.get("oasis_interest_3", holland_names[2])

    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        idx1 = holland_names.index(saved_i1) if saved_i1 in holland_names else 0
        interest_1 = st.selectbox(
            "Most Dominant",
            holland_names,
            index=idx1,
            key="sel_interest_1",
        )
        st.caption(HOLLAND_DESCRIPTIONS.get(interest_1, ""))

    # Exclude already-selected for 2nd pick
    opts_2 = [h for h in holland_names if h != interest_1]
    with col_i2:
        if saved_i2 in opts_2:
            idx2 = opts_2.index(saved_i2)
        else:
            idx2 = 0
        interest_2 = st.selectbox(
            "Second Dominant",
            opts_2,
            index=idx2,
            key="sel_interest_2",
        )
        st.caption(HOLLAND_DESCRIPTIONS.get(interest_2, ""))

    # Exclude both for 3rd pick
    opts_3 = [h for h in holland_names if h not in (interest_1, interest_2)]
    with col_i3:
        if saved_i3 in opts_3:
            idx3 = opts_3.index(saved_i3)
        else:
            idx3 = 0
        interest_3 = st.selectbox(
            "Third Dominant",
            opts_3,
            index=idx3,
            key="sel_interest_3",
        )
        st.caption(HOLLAND_DESCRIPTIONS.get(interest_3, ""))

    st.divider()

    # ── Confirm ───────────────────────────────────────────────
    if broad_field:
        if cip_code and cip_name:
            st.info(
                f"**CIP {cip_code}** — {cip_name}\n\n"
                f"Broad field: {broad_field}"
                + (f"  |  Data source: {subfield}" if subfield else "")
            )
        else:
            field_display = subfield or broad_field
            st.info(f"Selected field: **{field_display}**")
    else:
        st.warning("Please search or browse to select a field of study.")

    can_proceed = bool(broad_field)

    # CIP Employment Distribution button
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(
            "View Graduate Employment Distribution",
            use_container_width=True,
            disabled=not can_proceed,
            help="View 2yr and 5yr post-graduation income distribution for your CIP field",
        ):
            st.session_state["user_name"] = user_name
            st.session_state["user_age"] = user_age
            st.session_state["user_gender"] = user_gender
            st.session_state["broad_field"] = broad_field
            st.session_state["subfield"] = subfield
            st.session_state["cip_code"] = cip_code
            st.session_state["cip_name"] = cip_name
            st.session_state["education"] = education
            st.session_state["geo"] = geo
            st.session_state["_field_query"] = query
            # Save OaSIS interest selections and fetch matches
            st.session_state["oasis_interest_1"] = interest_1
            st.session_state["oasis_interest_2"] = interest_2
            st.session_state["oasis_interest_3"] = interest_3
            with st.spinner("Querying OaSIS interest matches..."):
                oasis_result = fetch_oasis_matches(interest_1, interest_2, interest_3)
            st.session_state["oasis_result"] = oasis_result
            st.session_state["wizard_page"] = "cip_distribution"
            st.rerun()

    with col_btn2:
        pass  # Visual balance

    st.divider()

    if st.button(
        "Confirm & View Analysis",
        type="primary",
        use_container_width=True,
        disabled=not can_proceed,
    ):
        st.session_state["user_name"] = user_name
        st.session_state["user_age"] = user_age
        st.session_state["user_gender"] = user_gender
        st.session_state["broad_field"] = broad_field
        st.session_state["subfield"] = subfield
        st.session_state["cip_code"] = cip_code
        st.session_state["cip_name"] = cip_name
        st.session_state["education"] = education
        st.session_state["geo"] = geo
        st.session_state["_field_query"] = query
        # Store the radio display_name so it can be re-selected on page revisit
        if query:
            _matches = match_fields(query, FIELD_OPTIONS)
            _opts = [m["display_name"] for m in _matches]
            for m in _matches:
                if m["broad_field"] == broad_field and m["subfield"] == subfield:
                    st.session_state["_selected_display"] = m["display_name"]
                    break
            else:
                st.session_state["_selected_display"] = (
                    f"{subfield}  ({broad_field})" if subfield else broad_field
                )
        else:
            st.session_state["_selected_display"] = (
                f"{subfield}  ({broad_field})" if subfield else broad_field
            )
        st.session_state["wizard_page"] = "analysis"
        st.rerun()


# ── Page 2: Analysis ──────────────────────────────────────────────


def _scroll_to_top():
    """Inject JS to scroll the main content area to the top."""
    st.components.v1.html(
        """<script>
        window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>""",
        height=0,
    )


def render_analysis_page():
    _scroll_to_top()

    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    # Initialize page2_data cache for deep analysis
    page2_data = st.session_state.get("page2_data", {})

    # ── Sidebar: user summary + edit button ───────────────────
    with st.sidebar:
        st.header("Your Profile")
        name = st.session_state.get("user_name", "")
        if name:
            st.write(f"**Name:** {name}")
        st.write(f"**Age:** {st.session_state.get('user_age', '—')}")
        st.write(f"**Gender:** {st.session_state.get('user_gender', '—')}")
        if cip_code and cip_name:
            st.write(f"**Major:** {cip_name} (CIP {cip_code})")
            st.write(f"**Broad field:** {broad_field}")
        else:
            st.write(f"**Field:** {field_display}")
        st.write(f"**Education:** {education}")
        st.write(f"**Province:** {geo}")
        st.divider()
        if st.button("Edit Profile", use_container_width=True):
            st.session_state["wizard_page"] = "profile"
            st.rerun()

    # ── Fixed header: title + navigation ─────────────────────
    sections = [
        ("sect-employment", "Employment Overview"),
        ("sect-income", "Income Analysis"),
        ("sect-unemployment", "Unemployment Trends"),
        ("sect-jobs", "Job Market"),
        ("sect-graduates", "Graduate Outcomes"),
    ]

    nav_links = "".join(
        f'<a href="#{sid}">{label}</a>'
        for sid, label in sections
    )

    st.markdown(
        '<div id="yf-header">'
        '  <h1>YF \u2014 Career Exploration</h1>'
        '  <p class="caption">'
        "Powered by Statistics Canada open data (live API queries)</p>"
        f'  <div class="nav">{nav_links}</div>'
        "</div>"
        '<div style="height:160px"></div>',
        unsafe_allow_html=True,
    )

    # ── Section 1: Employment Overview ────────────────────────
    st.markdown('<div id="sect-employment"></div>', unsafe_allow_html=True)
    st.header("Employment Overview")
    try:
        with st.spinner("Querying employment data..."):
            result = fetch_labour_force(broad_field, subfield, education, geo)
        page2_data["labour_force"] = result

        summary = result["summary"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Employment Rate", f"{summary.get('employment_rate', 'N/A')}%")
        col2.metric("Participation Rate", f"{summary.get('participation_rate', 'N/A')}%")
        col3.metric("Unemployment Rate", f"{summary.get('unemployment_rate', 'N/A')}%")

        chart_col1, chart_col2 = st.columns([3, 2])
        with chart_col1:
            st.plotly_chart(
                employment_rate_bar(result["comparison"], field_display),
                use_container_width=True,
            )
        with chart_col2:
            st.plotly_chart(
                education_comparison_grouped(summary, education),
                use_container_width=True,
            )

        emp_rate = summary.get("employment_rate", 50)
        unemp_rate = summary.get("unemployment_rate", 10)
        st.plotly_chart(
            radar_overview(
                employment_rate=min(emp_rate, 100),
                income_percentile=50,
                low_unemployment=max(0, 100 - unemp_rate * 5),
                vacancy_score=50,
                income_growth=50,
            ),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error loading employment data: {e}")
        st.code(traceback.format_exc())

    st.divider()

    # ── Section 2: Income Analysis ────────────────────────────
    st.markdown('<div id="sect-income"></div>', unsafe_allow_html=True)
    st.header("Income Analysis")
    try:
        with st.spinner("Querying income data..."):
            result = fetch_income(broad_field, subfield, education, geo)
        page2_data["income"] = result

        summary = result["summary"]
        col1, col2 = st.columns(2)
        median = summary.get("median_income")
        avg = summary.get("average_income")
        col1.metric("Median Income", f"${median:,.0f}" if median else "N/A")
        col2.metric("Average Income", f"${avg:,.0f}" if avg else "N/A")

        chart_col1, chart_col2 = st.columns([3, 2])
        with chart_col1:
            st.plotly_chart(
                income_ranking_bar(result["ranking"], field_display),
                use_container_width=True,
            )
        with chart_col2:
            st.plotly_chart(
                income_by_education_line(result["by_education"], field_display),
                use_container_width=True,
            )
    except Exception as e:
        st.error(f"Error loading income data: {e}")
        st.code(traceback.format_exc())

    st.divider()

    # ── Section 3: Unemployment Trends ────────────────────────
    st.markdown('<div id="sect-unemployment"></div>', unsafe_allow_html=True)
    st.header("Unemployment Trends")
    try:
        with st.spinner("Querying unemployment trends..."):
            result = fetch_unemployment_trends(education, geo)
        page2_data["unemployment"] = result

        summary = result["summary"]
        col1, col2 = st.columns(2)
        col1.metric("Current Rate", f"{summary.get('current_rate', 'N/A')}%")
        col2.metric("5-Year Average", f"{summary.get('five_yr_avg', 'N/A')}%")

        st.plotly_chart(
            unemployment_trend_lines(result["trends"], education),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error loading unemployment trends: {e}")
        st.code(traceback.format_exc())

    st.divider()

    # ── Section 4: Job Market ─────────────────────────────────
    st.markdown('<div id="sect-jobs"></div>', unsafe_allow_html=True)
    st.header("Job Market")
    try:
        with st.spinner("Querying job market data..."):
            result = fetch_job_vacancies(education, geo)
        page2_data["job_vacancies"] = result

        summary = result["summary"]
        col1, col2 = st.columns(2)
        vac = summary.get("vacancies")
        wage = summary.get("avg_wage")
        col1.metric("Latest Vacancies", f"{vac:,}" if vac else "N/A")
        col2.metric("Avg Offered Wage", f"${wage:,.2f}/hr" if wage else "N/A")

        st.plotly_chart(
            job_vacancy_dual_axis(result["trends"]),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error loading job market data: {e}")
        st.code(traceback.format_exc())

    st.divider()

    # ── Section 5: Graduate Outcomes ──────────────────────────
    st.markdown('<div id="sect-graduates"></div>', unsafe_allow_html=True)
    st.header("Graduate Outcomes")
    try:
        with st.spinner("Querying graduate outcomes..."):
            result = fetch_graduate_outcomes(broad_field, education, geo)
        page2_data["graduate_outcomes"] = result

        summary = result["summary"]
        col1, col2, col3 = st.columns(3)
        inc2 = summary.get("income_2yr")
        inc5 = summary.get("income_5yr")
        growth = summary.get("growth_pct")
        col1.metric("Income (2yr after)", f"${inc2:,.0f}" if inc2 else "N/A")
        col2.metric("Income (5yr after)", f"${inc5:,.0f}" if inc5 else "N/A")
        col3.metric("Growth", f"{growth:+.1f}%" if growth else "N/A")

        st.plotly_chart(
            graduate_income_trajectory(result["trajectory"]),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error loading graduate outcomes: {e}")
        st.code(traceback.format_exc())

    # Fetch subfield comparison data (silent — no visible section on Page 2)
    try:
        sf_result = fetch_subfield_comparison(broad_field, subfield, education, geo)
        page2_data["subfield_comparison"] = sf_result
    except Exception:
        pass

    # Cache page2_data for deep analysis
    st.session_state["page2_data"] = page2_data

    # Deep Analysis CTA
    st.divider()
    st.markdown(
        '<div class="yf-cta">'
        '<h3>Ready for deeper insights?</h3>'
        '<p>Composite scoring, trend forecasting, income projections, risk assessment, and education ROI</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "Launch Deep Career Analysis",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["wizard_page"] = "deep_analysis"
        st.rerun()

    # Footer
    st.divider()
    st.markdown(
        '<div class="yf-footer">Data source: Statistics Canada WDS REST API. '
        'Data is queried in real-time. Results are cached for 1 hour.</div>',
        unsafe_allow_html=True,
    )


# ── Page 3: Deep Career Analysis ─────────────────────────────────


def render_deep_analysis_page():
    _scroll_to_top()

    page2_data = st.session_state.get("page2_data", {})
    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    if not page2_data:
        st.warning("No data available. Please run the basic analysis first.")
        if st.button("Back to Analysis"):
            st.session_state["wizard_page"] = "analysis"
            st.rerun()
        return

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.header("Your Profile")
        name = st.session_state.get("user_name", "")
        if name:
            st.write(f"**Name:** {name}")
        st.write(f"**Age:** {st.session_state.get('user_age', '—')}")
        st.write(f"**Gender:** {st.session_state.get('user_gender', '—')}")
        if cip_code and cip_name:
            st.write(f"**Major:** {cip_name} (CIP {cip_code})")
            st.write(f"**Broad field:** {broad_field}")
        else:
            st.write(f"**Field:** {field_display}")
        st.write(f"**Education:** {education}")
        st.write(f"**Province:** {geo}")
        st.divider()
        if st.button("Back to Overview", use_container_width=True):
            st.session_state["wizard_page"] = "analysis"
            st.rerun()
        if st.button("Edit Profile", use_container_width=True, key="deep_edit"):
            st.session_state["wizard_page"] = "profile"
            st.rerun()

    # ── Run analysis ──────────────────────────────────────────
    with st.spinner("Running deep analysis algorithms..."):
        results = run_all_analyses(page2_data)

    # ── Fixed header ──────────────────────────────────────────
    sections = [
        ("deep-score", "Prospect Score"),
        ("deep-quadrant", "Career Quadrant"),
        ("deep-subfield", "Subfield Quadrant"),
        ("deep-forecast", "Trend Forecast"),
        ("deep-income", "Income Projection"),
        ("deep-risk", "Risk Assessment"),
        ("deep-roi", "Education ROI"),
        ("deep-compete", "Competitiveness"),
    ]

    nav_links = "".join(
        f'<a href="#{sid}">{label}</a>'
        for sid, label in sections
    )
    st.markdown(
        '<div id="yf-header">'
        '  <h1>YF — Deep Career Analysis</h1>'
        '  <p class="caption">'
        f"Advanced analysis for: {field_display} | {education} | {geo}</p>"
        f'  <div class="nav">{nav_links}</div>'
        "</div>"
        '<div style="height:160px"></div>',
        unsafe_allow_html=True,
    )

    # ── Section 1: Composite Career Prospect Score ────────────
    st.markdown('<div id="deep-score"></div>', unsafe_allow_html=True)
    st.header("Career Prospect Score")
    score = results["composite_score"]
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(composite_score_gauge(score), use_container_width=True)
    with col2:
        st.plotly_chart(component_radar(score), use_container_width=True)

    # Component breakdown
    components = score.get("components", {})
    cols = st.columns(len(components))
    for col, (name, val) in zip(cols, components.items()):
        col.metric(name, f"{val:.0f}/100")

    st.divider()

    # ── Section 2: Career Quadrant ────────────────────────────
    st.markdown('<div id="deep-quadrant"></div>', unsafe_allow_html=True)
    st.header("Career Quadrant — Employability vs Income")
    quadrant = results["career_quadrant"]
    if "error" not in quadrant:
        st.plotly_chart(career_quadrant_chart(quadrant), use_container_width=True)

        uq = quadrant.get("user_quadrant", "N/A")
        if "High Employability + High Income" in uq:
            st.success(f"**Your field:** {uq} — strong on both dimensions.")
        elif "High Income" in uq:
            st.info(f"**Your field:** {uq} — competitive entry but rewarding earnings.")
        elif "Accessible" in uq:
            st.info(f"**Your field:** {uq} — good job availability, room for income growth.")
        else:
            st.warning(f"**Your field:** {uq} — consider strategies to strengthen prospects.")

        st.caption(
            "Each dot is a field of study. The dashed lines split at the median across all fields. "
            "Your field is marked with a star."
        )
    else:
        st.warning(quadrant["error"])

    st.divider()

    # ── Section 2b: Subfield Quadrant ─────────────────────────
    st.markdown('<div id="deep-subfield"></div>', unsafe_allow_html=True)
    sf_quad = results["subfield_quadrant"]
    if "error" not in sf_quad:
        sf_broad = sf_quad.get("broad_field", broad_field)
        st.header(f"Within-Field Comparison — {sf_broad}")
        st.plotly_chart(subfield_quadrant_chart(sf_quad), use_container_width=True)

        sf_uq = sf_quad.get("user_quadrant", "N/A")
        if sf_uq != "N/A":
            if "High Employability + High Income" in sf_uq:
                st.success(f"**Among peers:** {sf_uq} — top subfield in your category.")
            elif "High Income" in sf_uq:
                st.info(f"**Among peers:** {sf_uq} — high earning but competitive entry.")
            elif "Accessible" in sf_uq:
                st.info(f"**Among peers:** {sf_uq} — easier entry, consider specialization for higher income.")
            else:
                st.warning(f"**Among peers:** {sf_uq} — may benefit from complementary skills or pivoting.")

        notes = []
        if sf_quad.get("has_estimated_emp"):
            notes.append(
                "Diamond markers indicate subfields where employment rate is estimated "
                "from a parent CIP category (exact data not available)."
            )
        notes.append(
            "Dashed lines split at the median of subfields within this broad field."
        )
        st.caption(" ".join(notes))
    else:
        st.header(f"Within-Field Comparison — {broad_field}")
        st.info(sf_quad["error"])

    st.divider()

    # ── Section 3: Trend Forecasts ────────────────────────────
    st.markdown('<div id="deep-forecast"></div>', unsafe_allow_html=True)
    st.header("Trend Forecasts")

    unemp_fc = results["unemployment_forecast"]
    vac_fc = results["vacancy_forecast"]

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(unemployment_forecast_chart(unemp_fc), use_container_width=True)
        if "interpretation" in unemp_fc:
            st.info(f"**Unemployment:** {unemp_fc['interpretation']}")
    with col2:
        st.plotly_chart(vacancy_forecast_chart(vac_fc), use_container_width=True)
        if "interpretation" in vac_fc:
            st.info(f"**Vacancies:** {vac_fc['interpretation']}")

    st.divider()

    # ── Section 3: Income Growth Projection ───────────────────
    st.markdown('<div id="deep-income"></div>', unsafe_allow_html=True)
    st.header("Income Growth Projection")
    proj = results["income_projection"]
    if "error" not in proj:
        st.plotly_chart(income_projection_chart(proj), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        dp = proj["data_points"]
        pp = proj["projected_points"]
        col1.metric("2yr Actual", f"${dp[0]['income']:,.0f}")
        col2.metric("5yr Actual", f"${dp[1]['income']:,.0f}")
        col3.metric(
            "10yr Projected",
            f"${pp[0]['income']:,.0f}",
            delta=f"+${pp[0]['income'] - dp[1]['income']:,.0f} from 5yr",
        )

        formula = proj["formula"]
        st.caption(
            f"Model: income = {formula['a']:,.2f} * ln(year) + {formula['b']:,.2f}"
        )
    else:
        st.warning(proj["error"])

    st.divider()

    # ── Section 4: Risk Assessment ────────────────────────────
    st.markdown('<div id="deep-risk"></div>', unsafe_allow_html=True)
    st.header("Career Stability & Risk Assessment")
    risk = results["risk_assessment"]
    st.plotly_chart(risk_assessment_chart(risk), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Volatility (CV%)", f"{risk['volatility_cv']:.1f}%" if risk.get("volatility_cv") is not None else "N/A")
    col2.metric("Income Symmetry", f"{risk['income_symmetry']:.3f}" if risk.get("income_symmetry") is not None else "N/A")
    col3.metric("Overall Stability", risk.get("overall_grade", "N/A"))

    st.info(risk.get("interpretation", ""))

    st.divider()

    # ── Section 5: Education ROI ──────────────────────────────
    st.markdown('<div id="deep-roi"></div>', unsafe_allow_html=True)
    st.header("Education ROI Analysis")
    roi = results["education_roi"]
    if "error" not in roi:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(education_roi_waterfall(roi), use_container_width=True)
        with col2:
            st.plotly_chart(break_even_timeline(roi), use_container_width=True)

        # Best ROI highlight
        best = roi.get("best_roi")
        if best:
            st.success(
                f"**Best ROI:** {best['from_level']} to {best['to_level']} — "
                f"${best['income_premium']:,.0f}/yr premium, "
                f"break-even in {best['break_even_years']:.1f} years"
            )

        # Detail table
        with st.expander("ROI Details"):
            for level in roi["levels"]:
                st.write(
                    f"**{level['from_level']} -> {level['to_level']}**: "
                    f"Premium ${level['income_premium']:,.0f}/yr ({level['premium_pct']:+.1f}%), "
                    f"Cost ${level['total_cost']:,.0f} over {level['duration_years']}yr, "
                    f"Break-even: {level['break_even_years']:.1f}yr" if level['break_even_years'] else
                    f"**{level['from_level']} -> {level['to_level']}**: "
                    f"No positive return"
                )
    else:
        st.warning(roi["error"])

    st.divider()

    # ── Section 6: Field Competitiveness ──────────────────────
    st.markdown('<div id="deep-compete"></div>', unsafe_allow_html=True)
    st.header("Field Competitiveness")
    compete = results["field_competitiveness"]
    if "error" not in compete:
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Employment Rank",
            f"#{compete['employment_rank']}" if compete.get("employment_rank") else "N/A",
            delta=compete.get("emp_quartile"),
        )
        col2.metric(
            "Income Rank",
            f"#{compete['income_rank']}" if compete.get("income_rank") else "N/A",
            delta=compete.get("inc_quartile"),
        )
        col3.metric("Total Fields", compete.get("total_fields", "N/A"))

        if compete.get("strengths"):
            st.success("**Strengths:** " + ", ".join(compete["strengths"]))
        if compete.get("weaknesses"):
            st.warning("**Weaknesses:** " + ", ".join(compete["weaknesses"]))
        if not compete.get("strengths") and not compete.get("weaknesses"):
            st.info("Your field ranks in the middle range across all metrics.")

        # Rankings table
        with st.expander("Full Field Rankings"):
            for i, fr in enumerate(compete["field_rankings"], 1):
                emp = f"{fr['employment_rate']:.1f}%" if fr.get("employment_rate") is not None else "N/A"
                inc = f"${fr['median_income']:,.0f}" if fr.get("median_income") is not None else "N/A"
                st.write(f"{i}. **{fr['field']}** — Employment: {emp}, Income: {inc}")
    else:
        st.warning(compete["error"])

    # Footer
    st.divider()
    st.markdown(
        '<div class="yf-footer">Deep analysis powered by algorithmic models applied to Statistics Canada data. '
        'Projections are estimates based on historical trends and should not be taken as guarantees.</div>',
        unsafe_allow_html=True,
    )


# ── Page: CIP Employment Distribution ─────────────────────────────


def render_cip_distribution_page():
    _scroll_to_top()

    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.header("Your Profile")
        name = st.session_state.get("user_name", "")
        if name:
            st.write(f"**Name:** {name}")
        st.write(f"**Age:** {st.session_state.get('user_age', '—')}")
        st.write(f"**Gender:** {st.session_state.get('user_gender', '—')}")
        if cip_code and cip_name:
            st.write(f"**Major:** {cip_name} (CIP {cip_code})")
            st.write(f"**Broad field:** {broad_field}")
        else:
            st.write(f"**Field:** {field_display}")
        st.write(f"**Education:** {education}")
        st.write(f"**Province:** {geo}")
        st.divider()
        if st.button("Back to Profile", use_container_width=True):
            st.session_state["wizard_page"] = "profile"
            st.rerun()

    # ── Header ─────────────────────────────────────────────────
    st.markdown(
        '<div id="yf-header">'
        '  <h1>YF — Graduate Employment Distribution</h1>'
        '  <p class="caption">'
        "Employment income, occupation direction (NOC), and proportions after graduation</p>"
        '  <div class="nav">'
        '    <a href="#sect-overview">Overview</a>'
        '    <a href="#sect-noc">Occupation (NOC)</a>'
        '    <a href="#sect-noc-detail">NOC Groups</a>'
        '    <a href="#sect-noc-specific">Specific Jobs</a>'
        '    <a href="#sect-quadrant">Quadrant</a>'
        '    <a href="#sect-broad">Income by Field</a>'
        '    <a href="#sect-subfield">Sub-fields</a>'
        '    <a href="#sect-growth">Growth Rate</a>'
        '  </div>'
        "</div>"
        '<div style="height:160px"></div>',
        unsafe_allow_html=True,
    )

    # Fetch both datasets
    try:
        with st.spinner("Querying graduate employment distribution data..."):
            result = fetch_cip_employment_distribution(cip_code, broad_field, education, geo)
    except Exception as e:
        st.error(f"Error loading CIP employment distribution: {e}")
        st.code(traceback.format_exc())
        return

    try:
        with st.spinner("Querying occupation (NOC) distribution data..."):
            noc_result = fetch_noc_distribution(cip_code, broad_field, education)
    except Exception as e:
        st.error(f"Error loading NOC distribution: {e}")
        st.code(traceback.format_exc())
        noc_result = None

    user_summary = result["user_summary"]
    user_field_name = result["user_field_name"]

    # ── OaSIS Interest Match Summary ──────────────────────────
    oasis_result = st.session_state.get("oasis_result")
    oasis_noc_set = set()
    if oasis_result and oasis_result.get("success") and oasis_result.get("noc_codes"):
        oasis_noc_set = set(oasis_result["noc_codes"])

        # Find overlapping NOCs between OaSIS results and CIP distribution
        if noc_result and noc_result.get("detail_distribution"):
            cip_noc_codes = set()
            for occ in noc_result["detail_distribution"]:
                code = occ["noc"].split(" ", 1)[0]
                cip_noc_codes.add(code)
            overlap = oasis_noc_set & cip_noc_codes

            if overlap:
                # Build display names for overlapping NOCs
                overlap_names = []
                for occ in noc_result["detail_distribution"]:
                    code = occ["noc"].split(" ", 1)[0]
                    if code in overlap:
                        overlap_names.append(occ["noc"])
                i1 = st.session_state.get("oasis_interest_1", "")
                i2 = st.session_state.get("oasis_interest_2", "")
                i3 = st.session_state.get("oasis_interest_3", "")
                match_list = "\n".join(f"- {n}" for n in overlap_names)
                st.success(
                    f"**OaSIS Interest Match Found!** Your interest profile "
                    f"({i1} > {i2} > {i3}) aligns with "
                    f"**{len(overlap)}** occupation(s) that graduates in your field actually enter:\n\n"
                    f"{match_list}"
                )
            else:
                i1 = st.session_state.get("oasis_interest_1", "")
                i2 = st.session_state.get("oasis_interest_2", "")
                i3 = st.session_state.get("oasis_interest_3", "")
                st.info(
                    f"**OaSIS Interest Search** ({i1} > {i2} > {i3}): "
                    f"Found {len(oasis_noc_set)} matching occupations, "
                    f"but none overlap with the top occupations for this field of study. "
                    f"The matched occupations are highlighted with \u2605 if they appear in the charts below."
                )
    elif oasis_result and not oasis_result.get("success"):
        st.warning(
            f"OaSIS interest search could not be completed: {oasis_result.get('error', 'Unknown error')}. "
            "Charts will display without interest highlights."
        )

    # ── Section: Overview ──────────────────────────────────────
    st.markdown('<div id="sect-overview"></div>', unsafe_allow_html=True)
    st.header("Your Field — Graduate Income Overview")

    if cip_code and cip_name:
        st.info(f"**CIP {cip_code}** — {cip_name}  →  Data mapped to: **{user_field_name}**")

    col1, col2, col3, col4 = st.columns(4)
    inc2 = user_summary.get("income_2yr")
    inc5 = user_summary.get("income_5yr")
    growth = user_summary.get("growth_pct")
    grad_count = user_summary.get("graduate_count")
    col1.metric("Income (2yr after)", f"${inc2:,.0f}" if inc2 else "N/A")
    col2.metric("Income (5yr after)", f"${inc5:,.0f}" if inc5 else "N/A")
    col3.metric("Growth (2yr→5yr)", f"{growth:+.1f}%" if growth is not None else "N/A")
    col4.metric("Graduate Count", f"{grad_count:,}" if grad_count else "N/A")

    st.divider()

    # ── Section: NOC Occupation Distribution ───────────────────
    st.markdown('<div id="sect-noc"></div>', unsafe_allow_html=True)
    st.header("Employment Direction — Occupation (NOC) Distribution")
    st.caption(
        "Where do graduates with this field of study actually work? "
        "This shows the distribution across NOC (National Occupational Classification) "
        "broad categories, based on 2021 Census data."
    )

    if noc_result and noc_result["broad_distribution"]:
        col_chart1, col_chart2 = st.columns([2, 3])
        with col_chart1:
            st.plotly_chart(
                noc_distribution_donut(noc_result["broad_distribution"]),
                use_container_width=True,
            )
        with col_chart2:
            st.plotly_chart(
                noc_distribution_bar(noc_result["broad_distribution"]),
                use_container_width=True,
            )

        # Show top 3 occupations as callouts
        top3 = noc_result["broad_distribution"][:3]
        cols = st.columns(len(top3))
        for col, occ in zip(cols, top3):
            cnt_str = f" ({occ['count']:,} people)" if occ.get("count") else ""
            col.metric(occ["noc"], f"{occ['percentage']:.1f}%", delta=cnt_str)

        # Not applicable info
        na_pct = noc_result.get("not_applicable_pct")
        if na_pct and na_pct > 0:
            na_cnt = noc_result.get("not_applicable_count")
            na_detail = f" ({na_cnt:,} people)" if na_cnt else ""
            st.caption(
                f"Note: {na_pct:.1f}% of graduates had no occupation classification{na_detail} "
                "(e.g., not in labour force, students, etc.)"
            )
    else:
        st.warning("No occupation distribution data available.")

    st.divider()

    # ── Section: NOC Detailed Sub-groups ───────────────────────
    st.markdown('<div id="sect-noc-detail"></div>', unsafe_allow_html=True)
    st.header("Detailed Occupation Groups (NOC 2-digit)")
    st.caption(
        "More granular breakdown of the top occupation sub-groups "
        "where graduates in this field are employed."
    )

    if noc_result and noc_result["submajor_distribution"]:
        st.plotly_chart(
            noc_submajor_bar(noc_result["submajor_distribution"]),
            use_container_width=True,
        )

        # Show full table in expander
        with st.expander("View all occupation groups"):
            for i, occ in enumerate(noc_result["submajor_distribution"], 1):
                cnt_str = f" — {occ['count']:,} people" if occ.get("count") else ""
                st.write(f"{i}. **{occ['noc']}**: {occ['percentage']:.1f}%{cnt_str}")
    else:
        st.info("No detailed occupation group data available.")

    st.divider()

    # ── Section: NOC 5-digit Specific Occupations ──────────────
    st.markdown('<div id="sect-noc-specific"></div>', unsafe_allow_html=True)
    st.header("Specific Occupations (NOC 5-digit)")
    st.caption(
        "The most specific occupation titles where graduates in this field work. "
        "Shows the top occupations with their NOC 2021 codes and proportions."
    )

    if noc_result and noc_result.get("detail_distribution"):
        st.plotly_chart(
            noc_detail_bar(noc_result["detail_distribution"], oasis_noc_set=oasis_noc_set),
            use_container_width=True,
        )

        # Show full table in expander
        with st.expander("View all specific occupations"):
            for i, occ in enumerate(noc_result["detail_distribution"], 1):
                code = occ["noc"].split(" ", 1)[0]
                oasis_marker = " \u2605 **OaSIS Match**" if code in oasis_noc_set else ""
                cnt_str = f" — {occ['count']:,} people" if occ.get("count") else ""
                st.write(f"{i}. **{occ['noc']}**: {occ['percentage']:.1f}%{cnt_str}{oasis_marker}")
    else:
        st.info("No specific occupation data available.")

    st.divider()

    # ── Section: Quadrant Bubble Chart ─────────────────────────
    st.markdown('<div id="sect-quadrant"></div>', unsafe_allow_html=True)
    st.header("Occupation Quadrant — Employment Count vs Income")
    st.caption(
        "Each bubble represents a specific occupation (5-digit NOC). "
        "X-axis: employment count (more people → further right). "
        "Y-axis: median income for age 25-64 (higher → more income). "
        "Bubble size: employment share (larger bubble = higher proportion of graduates)."
    )

    if noc_result and noc_result.get("detail_distribution"):
        try:
            with st.spinner("Querying income data for occupation quadrant..."):
                quadrant_data = fetch_noc_income_for_quadrant(
                    noc_result["detail_distribution"],
                    cip_code,
                    broad_field,
                    education,
                )
            if quadrant_data:
                st.plotly_chart(
                    noc_quadrant_bubble(quadrant_data, oasis_noc_set=oasis_noc_set),
                    use_container_width=True,
                )

                # Legend explanation
                st.markdown(
                    "**Quadrant Interpretation:**\n"
                    "- **Top-right (green):** Many people + high income — strong career paths\n"
                    "- **Top-left (indigo):** Fewer people + high income — specialized, less common\n"
                    "- **Bottom-right (amber):** Many people + lower income — accessible but lower-paying\n"
                    "- **Bottom-left (rose):** Fewer people + lower income — less common and lower-paying\n\n"
                    "*Larger bubbles indicate a higher proportion of graduates in that occupation.*"
                )
            else:
                st.info("Could not retrieve income data for the occupation quadrant chart.")
        except Exception as e:
            st.error(f"Error loading quadrant data: {e}")
            st.code(traceback.format_exc())
    else:
        st.info("No specific occupation data available for quadrant chart.")

    st.divider()

    # ── Section: Broad field income comparison ─────────────────
    st.markdown('<div id="sect-broad"></div>', unsafe_allow_html=True)
    st.header("Income by Field of Study — All Fields")
    st.caption(
        "Comparison of median employment income across all broad fields of study, "
        "2 years and 5 years after graduation. Your field is highlighted."
    )

    if result["broad_comparison"]:
        st.plotly_chart(
            cip_income_comparison_bar(result["broad_comparison"], broad_field),
            use_container_width=True,
        )
    else:
        st.warning("No broad field comparison data available.")

    st.divider()

    # ── Section: Sub-field comparison ──────────────────────────
    st.markdown('<div id="sect-subfield"></div>', unsafe_allow_html=True)
    st.header(f"Sub-field Breakdown — {broad_field}")
    st.caption(
        f"Detailed income comparison within the '{broad_field}' category."
    )

    if result["subfield_comparison"]:
        st.plotly_chart(
            cip_subfield_income_bar(result["subfield_comparison"], user_field_name),
            use_container_width=True,
        )
    else:
        st.info("No sub-field data available for this broad category.")

    st.divider()

    # ── Section: Growth rate comparison ────────────────────────
    st.markdown('<div id="sect-growth"></div>', unsafe_allow_html=True)
    st.header("Income Growth Rate — 2yr to 5yr After Graduation")
    st.caption(
        "Percentage increase in median income from 2 years to 5 years after graduation. "
        "Higher growth rates indicate stronger career trajectory early on."
    )

    if result["broad_comparison"]:
        st.plotly_chart(
            cip_growth_bar(result["broad_comparison"], broad_field),
            use_container_width=True,
        )
    else:
        st.warning("No growth rate data available.")

    # ── Navigation ─────────────────────────────────────────────
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Profile", use_container_width=True, key="cip_back_profile"):
            st.session_state["wizard_page"] = "profile"
            st.rerun()
    with col2:
        if st.button(
            "Continue to Full Analysis",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["wizard_page"] = "analysis"
            st.rerun()

    # Footer
    st.divider()
    st.markdown(
        '<div class="yf-footer">Data sources: Statistics Canada Table 37-10-0280-01 '
        '(Graduate income by CIP field), Table 98-10-0403-01 '
        '(Occupation by field of study), and Table 98-10-0412-01 '
        '(Income by NOC and CIP, 2021 Census). '
        'Queried in real-time via WDS REST API.</div>',
        unsafe_allow_html=True,
    )


# ── Router ────────────────────────────────────────────────────────


def main():
    if "wizard_page" not in st.session_state:
        st.session_state["wizard_page"] = "profile"

    page = st.session_state["wizard_page"]
    if page == "deep_analysis":
        render_deep_analysis_page()
    elif page == "cip_distribution":
        render_cip_distribution_page()
    elif page == "analysis":
        render_analysis_page()
    else:
        render_profile_page()


if __name__ == "__main__":
    main()
