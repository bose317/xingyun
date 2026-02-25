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
    fetch_noc_gender_breakdown,
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
from oasis_client import (
    fetch_oasis_matches, fetch_noc_description, fetch_noc_unit_profile,
    fetch_jobbank_skills, fetch_jobbank_wages,
    HOLLAND_CODES, HOLLAND_DESCRIPTIONS,
)
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
    col_btn1, _ = st.columns([2, 1])
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
                match_items = "".join(f"<li>{n}</li>" for n in overlap_names)
                st.markdown(
                    f'<div class="yf-oasis-banner">'
                    f'<h4>OaSIS Interest Match Found!</h4>'
                    f'<p>Your interest profile ({i1} &gt; {i2} &gt; {i3}) aligns with '
                    f'<strong>{len(overlap)}</strong> occupation(s) that graduates in your field actually enter:</p>'
                    f'<ul>{match_items}</ul>'
                    f'</div>',
                    unsafe_allow_html=True,
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
            st.caption("Hover over slices for detailed breakdowns.")
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

                # Compact quadrant legend
                q1, q2, q3, q4 = st.columns(4)
                q1.markdown(
                    '<span style="color:#10B981;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Many + High Pay</span>',
                    unsafe_allow_html=True,
                )
                q2.markdown(
                    '<span style="color:#6366F1;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Few + High Pay</span>',
                    unsafe_allow_html=True,
                )
                q3.markdown(
                    '<span style="color:#F59E0B;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Many + Lower Pay</span>',
                    unsafe_allow_html=True,
                )
                q4.markdown(
                    '<span style="color:#F43F5E;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Few + Lower Pay</span>',
                    unsafe_allow_html=True,
                )
                st.caption("Bubble size = share of graduates. Hover for details.")
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


# ── New Page: Career Exploration ──────────────────────────────────


def render_career_exploration_page():
    st.title("Career Exploration")

    # ── Step 1: Tell us about yourself ─────────────────────
    st.subheader("Step 1: Tell us about yourself")

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input(
            "Name",
            value=st.session_state.get("user_name", ""),
            key="ce_name",
        )
    with col2:
        user_age = st.slider(
            "Age",
            min_value=16,
            max_value=70,
            value=st.session_state.get("user_age", 25),
            key="ce_age",
        )

    col3, col4 = st.columns(2)
    with col3:
        gender_options = ["Male", "Female", "Other"]
        gender_idx = 0
        saved_gender = st.session_state.get("user_gender")
        if saved_gender in gender_options:
            gender_idx = gender_options.index(saved_gender)
        user_gender = st.selectbox("Gender", gender_options, index=gender_idx, key="ce_gender")
    with col4:
        edu_keys = list(EDUCATION_OPTIONS.keys())
        edu_idx = 0
        saved_edu = st.session_state.get("education")
        if saved_edu in edu_keys:
            edu_idx = edu_keys.index(saved_edu)
        education = st.selectbox("Education Level", edu_keys, index=edu_idx, key="ce_edu")

    geo_idx = 0
    saved_geo = st.session_state.get("geo")
    if saved_geo in GEO_OPTIONS:
        geo_idx = GEO_OPTIONS.index(saved_geo)
    geo = st.selectbox("Province / Territory", GEO_OPTIONS, index=geo_idx, key="ce_geo")

    st.divider()

    # ── Step 2: Field of Study ─────────────────────────────
    st.subheader("Step 2: Field of Study")

    # If Browse was just used, clear the search box
    if st.session_state.pop("_ce_clear_search", False):
        _query_default = ""
    else:
        _query_default = st.session_state.get("_ce_field_query", "")

    # Search input + Browse button side by side
    search_col, browse_col = st.columns([5, 1])
    with search_col:
        query = st.text_input(
            "Search by keyword or CIP code (e.g. 'computer science', '14.08')",
            value=_query_default,
            key="ce_field_query",
        )
    with browse_col:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        browse_open = st.button(
            "Browse",
            key="ce_browse_toggle",
            help="If you don't know your major name or CIP code, look it up here",
            use_container_width=True,
        )

    # Track browse panel state
    if browse_open:
        st.session_state["_ce_browse_open"] = not st.session_state.get("_ce_browse_open", False)

    broad_field = st.session_state.get("broad_field")
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")

    if query:
        matches = match_fields(query, FIELD_OPTIONS)
        if matches:
            options = [m["display_name"] for m in matches]
            preselect = 0
            saved_display = st.session_state.get("_selected_display")
            if saved_display in options:
                preselect = options.index(saved_display)

            choice = st.radio(
                "Select your field:",
                options,
                index=preselect,
                key="ce_field_radio",
            )
            selected = matches[options.index(choice)]
            broad_field = selected["broad_field"]
            subfield = selected["subfield"]
            cip_code = selected.get("cip_code")
            cip_name = selected.get("cip_name")

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
            st.warning("No matches found. Try a different keyword or browse using the button above.")
            broad_field = None
            subfield = None
            cip_code = None
            cip_name = None

    # Browse all fields panel (shown as expander when toggled)
    if st.session_state.get("_ce_browse_open", False):
        with st.expander("Browse all fields", expanded=True):
            # ── Level 1: Broad field ──
            broad_fields = list(FIELD_OPTIONS.keys())
            browse_idx = 0
            if broad_field in broad_fields:
                browse_idx = broad_fields.index(broad_field)
            browse_broad = st.selectbox(
                "Broad field",
                broad_fields,
                index=browse_idx,
                key="ce_browse_broad",
            )

            # ── Level 2: CIP series (2-digit) ──
            series_for_broad = sorted(
                code for code, bf in CIP_TO_BROAD.items() if bf == browse_broad
            )
            series_options = {
                code: f"{code}. {CIP_SERIES.get(code, code)}"
                for code in series_for_broad
                if code in CIP_SERIES
            }
            chosen_series = None
            if series_options:
                series_labels = ["(All series)"] + list(series_options.values())
                series_choice = st.selectbox(
                    "Series (2-digit CIP)",
                    series_labels,
                    key="ce_browse_series",
                )
                if series_choice != "(All series)":
                    for code, label in series_options.items():
                        if label == series_choice:
                            chosen_series = code
                            break

            # ── Level 3: Subseries (4-digit) ──
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
                        key="ce_browse_sub4",
                    )
                    if sub4_choice != "(All subseries)":
                        chosen_subseries = sub4_choice.split(" ", 1)[0]

            # ── Level 4: Class (6-digit) ──
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
                        key="ce_browse_cls6",
                    )
                    if cls_choice != "(All programs)":
                        chosen_class = cls_choice.split(" ", 1)[0]

            if st.button("Use this field", key="ce_use_browse"):
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
                st.session_state["broad_field"] = _bf
                st.session_state["subfield"] = _sf
                st.session_state["cip_code"] = _cc
                st.session_state["cip_name"] = _cn
                st.session_state["_ce_field_query"] = ""
                st.session_state["_ce_clear_search"] = True
                st.session_state["_ce_browse_open"] = False
                st.rerun()

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

    if st.button(
        "Confirm & View Analysis",
        type="primary",
        use_container_width=True,
        disabled=not can_proceed,
        key="ce_confirm",
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
        st.session_state["_ce_field_query"] = query
        if query:
            _matches = match_fields(query, FIELD_OPTIONS)
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
        st.session_state["wizard_page"] = "ce_analysis"
        st.rerun()


# ── New Page: CE Analysis ────────────────────────────────────────


def render_ce_analysis_page():
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
        if st.button("Back to Career Exploration", use_container_width=True, key="ce_back"):
            st.session_state["wizard_page"] = "career_exploration"
            st.rerun()

    # ── Header ─────────────────────────────────────────────────
    st.title("Career Exploration — Analysis")
    if cip_code and cip_name:
        st.info(f"**CIP {cip_code}** — {cip_name}  |  Broad field: **{broad_field}**")
    else:
        st.info(f"Field of study: **{field_display}**")

    # ── Fetch NOC distribution data ───────────────────────────
    noc_result = None
    try:
        with st.spinner("Querying occupation (NOC) distribution data..."):
            noc_result = fetch_noc_distribution(cip_code, broad_field, education)
    except Exception as e:
        st.error(f"Error loading NOC distribution: {e}")
        st.code(traceback.format_exc())

    if not noc_result:
        st.warning("No occupation distribution data available.")
        return

    # ── Chart 1: Detailed Occupation Groups (NOC 2-digit) ─────
    st.header("Detailed Occupation Groups (NOC 2-digit)")
    st.caption(
        "Granular breakdown of the top occupation sub-groups "
        "where graduates in this field are employed."
    )

    if noc_result.get("submajor_distribution"):
        st.plotly_chart(
            noc_submajor_bar(noc_result["submajor_distribution"]),
            use_container_width=True,
        )
    else:
        st.info("No detailed occupation group data available.")

    st.divider()

    # ── Chart 2: Specific Occupations (NOC 5-digit) ───────────
    st.header("Specific Occupations (NOC 5-digit)")
    st.caption(
        "The most specific occupation titles where graduates in this field work, "
        "with their NOC 2021 codes and proportions."
    )

    if noc_result.get("detail_distribution"):
        st.plotly_chart(
            noc_detail_bar(noc_result["detail_distribution"]),
            use_container_width=True,
        )
    else:
        st.info("No specific occupation data available.")

    st.divider()

    # ── Top 5 NOC occupations with gender breakdown ───────────
    st.header("Top 5 Occupations — Detailed Headcount")
    st.caption(
        "Employment headcount breakdown (Total / Male / Female) for the top 5 "
        "specific occupations that graduates in this field enter."
    )

    # Use 5-digit detail if available, otherwise fall back to 2-digit
    top_entries = noc_result.get("detail_distribution") or noc_result.get("submajor_distribution") or []

    if top_entries:
        try:
            with st.spinner("Querying gender breakdown for top occupations..."):
                gender_data = fetch_noc_gender_breakdown(
                    top_entries, cip_code, broad_field, education, top_n=5
                )
        except Exception as e:
            st.error(f"Error loading gender breakdown: {e}")
            st.code(traceback.format_exc())
            gender_data = []

        if gender_data:
            # Fetch OaSIS descriptions for all top NOCs
            noc_desc_data = {}  # full_name -> {description, sub_profiles}
            noc_codes_to_fetch = []
            for item in gender_data:
                code = item["noc"].split(" ", 1)[0]  # e.g. "41221"
                if len(code) == 5 and code.isdigit():
                    noc_codes_to_fetch.append((code, item["noc"]))

            if noc_codes_to_fetch:
                with st.spinner("Fetching occupation descriptions from OaSIS..."):
                    for code, full_name in noc_codes_to_fetch:
                        info = fetch_noc_description(code)
                        if info and (info.get("description") or info.get("sub_profiles")):
                            noc_desc_data[full_name] = info

            for i, item in enumerate(gender_data, 1):
                noc_name = item["noc"]
                total = item["count_total"]
                male = item["count_male"]
                female = item["count_female"]

                total_str = f"{total:,}" if total is not None else "N/A"
                male_str = f"{male:,}" if male is not None else "N/A"
                female_str = f"{female:,}" if female is not None else "N/A"

                st.markdown(f"**{i}. {noc_name}**")

                # Show OaSIS description and/or sub-profiles
                info = noc_desc_data.get(noc_name)
                if info:
                    desc = info.get("description")
                    subs = info.get("sub_profiles") or []

                    if desc:
                        # Direct description available
                        st.markdown(
                            f"<div style='background:#F8FAFC; border-left:3px solid #6366F1; "
                            f"padding:10px 14px; margin:6px 0 10px; border-radius:0 8px 8px 0; "
                            f"color:#475569; font-size:0.9rem; line-height:1.5;'>"
                            f"{desc}</div>",
                            unsafe_allow_html=True,
                        )

                    if subs:
                        # Build sub-profile HTML
                        sub_items = ""
                        for sub in subs:
                            sub_code = sub["code"]
                            sub_title = sub["title"]
                            sub_desc = sub.get("description") or ""
                            desc_html = (
                                f"<div style='color:#475569; font-size:0.85rem; "
                                f"margin:2px 0 6px 18px; line-height:1.4;'>{sub_desc}</div>"
                                if sub_desc else ""
                            )
                            sub_items += (
                                f"<div style='margin-bottom:6px;'>"
                                f"<span style='color:#6366F1; font-weight:600; font-size:0.88rem;'>"
                                f"{sub_code}</span>"
                                f" — <span style='font-weight:500; font-size:0.88rem;'>"
                                f"{sub_title}</span>"
                                f"{desc_html}</div>"
                            )
                        st.markdown(
                            f"<div style='background:#F8FAFC; border-left:3px solid #A855F7; "
                            f"padding:10px 14px; margin:6px 0 10px; border-radius:0 8px 8px 0;'>"
                            f"<div style='color:#7C3AED; font-weight:600; font-size:0.82rem; "
                            f"margin-bottom:8px; text-transform:uppercase; letter-spacing:0.03em;'>"
                            f"Occupational Profiles</div>"
                            f"{sub_items}</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"Total: **{total_str}**&emsp;|&emsp;"
                    f"Male: **{male_str}**&emsp;|&emsp;"
                    f"Female: **{female_str}**"
                )
                if i < len(gender_data):
                    st.markdown("---")
        else:
            st.info("Gender breakdown data not available for these occupations.")
    else:
        st.info("No occupation data available to show headcount breakdown.")

    # ── Career Analysis button ────────────────────────────────
    st.divider()

    # Save top NOC codes for the next page
    top_noc_codes = []
    top_entries_src = noc_result.get("detail_distribution") or noc_result.get("submajor_distribution") or []
    for entry in top_entries_src[:5]:
        code = entry["noc"].split(" ", 1)[0]
        if len(code) == 5 and code.isdigit():
            top_noc_codes.append({"code": code, "name": entry["noc"]})

    if top_noc_codes:
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button(
                "View Job Title Details",
                type="primary",
                use_container_width=True,
                key="ce_career_analysis_btn",
            ):
                st.session_state["ce_top_nocs"] = top_noc_codes
                st.session_state["wizard_page"] = "ce_job_analysis"
                st.rerun()
        with btn_col2:
            if st.button(
                "View Required Skills",
                type="primary",
                use_container_width=True,
                key="ce_skills_btn",
            ):
                st.session_state["ce_top_nocs"] = top_noc_codes
                st.session_state["wizard_page"] = "ce_skills"
                st.rerun()
        with btn_col3:
            if st.button(
                "View Income Analysis",
                type="primary",
                use_container_width=True,
                key="ce_wages_btn",
            ):
                st.session_state["ce_top_nocs"] = top_noc_codes
                st.session_state["wizard_page"] = "ce_wages"
                st.rerun()


# ── New Page: CE Job Analysis ────────────────────────────────────


def render_ce_job_analysis_page():
    _scroll_to_top()

    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    top_nocs = st.session_state.get("ce_top_nocs", [])

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
        if st.button("Back to Analysis", use_container_width=True, key="job_back_analysis"):
            st.session_state["wizard_page"] = "ce_analysis"
            st.rerun()
        if st.button("Back to Career Exploration", use_container_width=True, key="job_back_ce"):
            st.session_state["wizard_page"] = "career_exploration"
            st.rerun()

    # ── Header ─────────────────────────────────────────────────
    st.title("Career Analysis — Job Title Profiles")
    if cip_code and cip_name:
        st.info(f"**CIP {cip_code}** — {cip_name}")
    st.caption(
        "Detailed unit group profiles for the top occupations that graduates "
        "in this field enter. Data from the National Occupational Classification (NOC)."
    )

    if not top_nocs:
        st.warning("No occupation data available. Please go back and run the analysis first.")
        return

    # ── Fetch all profiles ────────────────────────────────────
    profiles = {}
    with st.spinner("Fetching unit group profiles from NOC..."):
        for noc in top_nocs:
            profiles[noc["code"]] = fetch_noc_unit_profile(noc["code"])

    # ── Profile sections to display ───────────────────────────
    PROFILE_ROWS = [
        ("example_titles", "Example Titles"),
        ("main_duties", "Main Duties"),
        ("employment_requirements", "Employment Requirements"),
        ("additional_information", "Additional Information"),
        ("exclusions", "Exclusions"),
    ]

    # ── Build comparison table ────────────────────────────────
    # Column headers: one per NOC
    noc_codes = [n["code"] for n in top_nocs]
    noc_labels = []
    for n in top_nocs:
        p = profiles.get(n["code"], {})
        title = p.get("title") or n["name"].split(" ", 1)[-1] if " " in n["name"] else n["name"]
        noc_labels.append(f"**{n['code']}**<br>{title}")

    # Render as styled HTML table
    # Build header
    header_cells = "".join(
        f"<th style='background:linear-gradient(135deg,#6366F1,#8B5CF6); color:white; "
        f"padding:12px 10px; font-size:0.82rem; font-weight:600; text-align:center; "
        f"min-width:180px; border-right:1px solid rgba(255,255,255,0.2);'>"
        f"{profiles.get(n['code'], {}).get('title') or n['name']}<br>"
        f"<span style='font-weight:400; opacity:0.85;'>NOC {n['code']}</span></th>"
        for n in top_nocs
    )

    # Build rows
    rows_html = ""
    for field_key, field_label in PROFILE_ROWS:
        cells = ""
        for n in top_nocs:
            p = profiles.get(n["code"], {})
            items = p.get(field_key) or []

            if items:
                items_html = "".join(
                    f"<li style='margin-bottom:3px;'>{item}</li>" for item in items
                )
                cell_content = f"<ul style='margin:0; padding-left:16px; font-size:0.82rem; line-height:1.45;'>{items_html}</ul>"
            else:
                cell_content = "<span style='color:#94A3B8; font-style:italic; font-size:0.82rem;'>N/A</span>"

            cells += (
                f"<td style='padding:10px 12px; vertical-align:top; "
                f"border-bottom:1px solid #E2E8F0; border-right:1px solid #F1F5F9;'>"
                f"{cell_content}</td>"
            )

        rows_html += (
            f"<tr>"
            f"<td style='padding:10px 12px; font-weight:600; color:#4338CA; "
            f"background:#F8FAFC; vertical-align:top; white-space:nowrap; "
            f"border-bottom:1px solid #E2E8F0; border-right:1px solid #E2E8F0; "
            f"font-size:0.85rem;'>{field_label}</td>"
            f"{cells}</tr>"
        )

    table_html = (
        f"<div style='overflow-x:auto; border:1px solid #E2E8F0; border-radius:12px; "
        f"box-shadow:0 1px 3px rgba(0,0,0,0.04);'>"
        f"<table style='width:100%; border-collapse:collapse; table-layout:fixed;'>"
        f"<thead><tr>"
        f"<th style='background:#1E293B; color:white; padding:12px; font-size:0.82rem; "
        f"font-weight:600; text-align:left; min-width:140px; "
        f"border-right:1px solid rgba(255,255,255,0.15);'>Profile</th>"
        f"{header_cells}"
        f"</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>"
    )

    st.markdown(table_html, unsafe_allow_html=True)


# ── New Page: CE Skills ──────────────────────────────────────────


def render_ce_skills_page():
    _scroll_to_top()

    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    top_nocs = st.session_state.get("ce_top_nocs", [])

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
        if st.button("Back to Analysis", use_container_width=True, key="skills_back_analysis"):
            st.session_state["wizard_page"] = "ce_analysis"
            st.rerun()
        if st.button("Back to Career Exploration", use_container_width=True, key="skills_back_ce"):
            st.session_state["wizard_page"] = "career_exploration"
            st.rerun()

    # ── Header ─────────────────────────────────────────────────
    st.title("Career Exploration — Required Skills")
    if cip_code and cip_name:
        st.info(f"**CIP {cip_code}** — {cip_name}  |  Location: **{geo}**")
    st.caption(
        "Skills, work styles, and knowledge requirements for the top occupations. "
        "Data from Job Bank Canada (jobbank.gc.ca)."
    )

    if not top_nocs:
        st.warning("No occupation data available. Please go back and run the analysis first.")
        return

    # ── Fetch skills for all NOCs ─────────────────────────────
    all_skills = {}
    with st.spinner("Fetching skills data from Job Bank..."):
        for noc in top_nocs:
            all_skills[noc["code"]] = fetch_jobbank_skills(noc["code"], geo)

    # Check if we got any data
    has_data = any(
        s.get("skills") or s.get("work_styles") or s.get("knowledge")
        for s in all_skills.values()
    )
    if not has_data:
        st.warning("Could not retrieve skills data from Job Bank for these occupations.")
        return

    # ── Build comparison tables for each section ──────────────
    SECTIONS = [
        ("skills", "Skills", "Proficiency / Complexity Level"),
        ("work_styles", "Work Styles", "Importance"),
        ("knowledge", "Knowledge", "Knowledge Level"),
    ]

    # Build header cells (same for all tables)
    header_cells = ""
    for n in top_nocs:
        s = all_skills.get(n["code"], {})
        title = s.get("title") or n["name"].split(" ", 1)[-1] if " " in n["name"] else n["name"]
        header_cells += (
            f"<th style='background:linear-gradient(135deg,#6366F1,#8B5CF6); color:white; "
            f"padding:5px 4px; font-size:0.7rem; font-weight:600; text-align:center; "
            f"min-width:90px; border-right:1px solid rgba(255,255,255,0.2);'>"
            f"{title}<br>"
            f"<span style='font-weight:400; opacity:0.8; font-size:0.65rem;'>NOC {n['code']}</span></th>"
        )

    for section_key, section_title, level_label in SECTIONS:
        st.header(section_title)
        st.caption(f"Comparison of {section_title.lower()} across occupations — {level_label}")

        # Collect all unique skill names across NOCs for this section
        all_names = []
        seen = set()
        for n in top_nocs:
            s = all_skills.get(n["code"], {})
            for item in s.get(section_key, []):
                if item["name"] not in seen:
                    seen.add(item["name"])
                    all_names.append(item["name"])

        if not all_names:
            st.info(f"No {section_title.lower()} data available.")
            st.divider()
            continue

        # Build skill lookup per NOC: name → level
        noc_lookups = {}
        for n in top_nocs:
            s = all_skills.get(n["code"], {})
            lookup = {}
            for item in s.get(section_key, []):
                lookup[item["name"]] = item["level"]
            noc_lookups[n["code"]] = lookup

        # Color maps: red (highest) → gray (lowest)
        # Skills & Work Styles: 1-5;  Knowledge: 1-3
        _COLORS_5 = {
            5: "#DC2626",   # red
            4: "#EA580C",   # orange
            3: "#D97706",   # amber
            2: "#8B6C4F",   # brown
            1: "#9CA3AF",   # gray
        }
        _COLORS_3 = {
            3: "#DC2626",   # red
            2: "#8B6C4F",   # brown
            1: "#9CA3AF",   # gray
        }
        is_knowledge = section_key == "knowledge"
        color_map = _COLORS_3 if is_knowledge else _COLORS_5
        max_score = 3 if is_knowledge else 5

        def _badge(value):
            """Return HTML for a colored number badge."""
            clr = color_map.get(round(value), "#9CA3AF")
            display = str(int(value))
            return (
                f"<span style='display:inline-block; min-width:22px; text-align:center; "
                f"background:{clr}; color:#FFF; padding:2px 6px; border-radius:5px; "
                f"font-size:0.78rem; font-weight:700; line-height:1.3;'>{display}</span>"
            )

        def _avg_bar(value):
            """Return HTML for Avg column: bar + number."""
            clr = color_map.get(round(value), "#9CA3AF")
            pct = value / max_score * 100
            display = f"{value:.1f}" if value != int(value) else str(int(value))
            return (
                f"<div style='display:flex; align-items:center; gap:5px; min-width:90px;'>"
                f"<div style='flex:1; background:#E5E7EB; border-radius:4px; height:10px; overflow:hidden;'>"
                f"<div style='width:{pct:.0f}%; height:100%; background:{clr}; "
                f"border-radius:4px;'></div></div>"
                f"<span style='font-size:0.78rem; font-weight:700; color:{clr}; "
                f"min-width:24px; text-align:right;'>{display}</span></div>"
            )

        # Build rows
        rows_html = ""
        for skill_name in all_names:
            noc_cells = ""
            scores = []
            for n in top_nocs:
                level = noc_lookups[n["code"]].get(skill_name)
                if level:
                    num_int = int(level[0]) if level[0].isdigit() else 0
                    scores.append(num_int)
                    cell_content = _badge(num_int)
                else:
                    cell_content = "<span style='color:#CBD5E1; font-size:0.75rem;'>—</span>"
                noc_cells += (
                    f"<td style='padding:3px 4px; text-align:center; vertical-align:middle; "
                    f"border-bottom:1px solid #E2E8F0; border-right:1px solid #F1F5F9;'>"
                    f"{cell_content}</td>"
                )

            # Average cell (placed right after label)
            if scores:
                avg = sum(scores) / len(scores)
                avg_content = _avg_bar(avg)
            else:
                avg_content = "<span style='color:#CBD5E1; font-size:0.75rem;'>—</span>"
            avg_cell = (
                f"<td style='padding:3px 8px; vertical-align:middle; "
                f"border-bottom:1px solid #E2E8F0; border-right:2px solid #E2E8F0; "
                f"background:#F1F5F9;'>{avg_content}</td>"
            )

            rows_html += (
                f"<tr>"
                f"<td style='padding:3px 8px; font-weight:500; color:#1E293B; "
                f"background:#FAFBFC; vertical-align:middle; "
                f"border-bottom:1px solid #E2E8F0; border-right:1px solid #E2E8F0; "
                f"font-size:0.8rem; line-height:1.3;'>{skill_name}</td>"
                f"{avg_cell}{noc_cells}</tr>"
            )

        # Avg column header (right after label)
        avg_header = (
            "<th style='background:#374151; color:#FDE68A; "
            "padding:6px 8px; font-size:0.8rem; font-weight:700; text-align:center; "
            "min-width:110px; border-right:2px solid rgba(255,255,255,0.3);'>Avg</th>"
        )

        # Fixed column widths for consistency across all 3 tables
        n_nocs = len(top_nocs)
        col_defs = (
            "<colgroup>"
            "<col style='width:200px;'/>"   # label
            "<col style='width:130px;'/>"   # avg
            + "".join(f"<col style='width:80px;'/>" for _ in range(n_nocs))
            + "</colgroup>"
        )

        table_html = (
            f"<div style='overflow-x:auto; border:1px solid #E2E8F0; border-radius:12px; "
            f"box-shadow:0 1px 3px rgba(0,0,0,0.04); margin-bottom:8px;'>"
            f"<table style='width:100%; border-collapse:collapse; table-layout:fixed;'>"
            f"{col_defs}"
            f"<thead><tr>"
            f"<th style='background:#1E293B; color:white; padding:6px 8px; font-size:0.8rem; "
            f"font-weight:600; text-align:left; "
            f"border-right:1px solid rgba(255,255,255,0.15);'>{level_label}</th>"
            f"{avg_header}{header_cells}"
            f"</tr></thead>"
            f"<tbody>{rows_html}</tbody>"
            f"</table></div>"
        )

        st.markdown(table_html, unsafe_allow_html=True)

        # Legend — colored bars
        if is_knowledge:
            legend_items = [
                ("3", "#DC2626", "Advanced"),
                ("2", "#8B6C4F", "Intermediate"),
                ("1", "#9CA3AF", "Basic"),
            ]
        else:
            legend_items = [
                ("5", "#DC2626", "Highest"),
                ("4", "#EA580C", "High"),
                ("3", "#D97706", "Moderate"),
                ("2", "#8B6C4F", "Low"),
                ("1", "#9CA3AF", "Basic"),
            ]
        legend_html = "".join(
            f"<span style='display:inline-flex; align-items:center; margin-right:16px;'>"
            f"<span style='display:inline-block; width:24px; height:10px; "
            f"background:{clr}; border-radius:3px; margin-right:5px;'></span>"
            f"<span style='color:#475569; font-size:0.75rem;'>{num} {label}</span></span>"
            for num, clr, label in legend_items
        )
        st.markdown(
            f"<div style='margin-bottom:16px;'>{legend_html}</div>",
            unsafe_allow_html=True,
        )
        st.divider()


# ── New Page: CE Wages / Income Analysis ─────────────────────────


def render_ce_wages_page():
    _scroll_to_top()

    broad_field = st.session_state.get("broad_field") or "Total"
    subfield = st.session_state.get("subfield")
    cip_code = st.session_state.get("cip_code")
    cip_name = st.session_state.get("cip_name")
    education = st.session_state.get("education", "Bachelor's degree")
    geo = st.session_state.get("geo", "Canada")
    field_display = subfield or broad_field

    top_nocs = st.session_state.get("ce_top_nocs", [])

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
        if st.button("Back to Analysis", use_container_width=True, key="wages_back_analysis"):
            st.session_state["wizard_page"] = "ce_analysis"
            st.rerun()
        if st.button("Back to Career Exploration", use_container_width=True, key="wages_back_ce"):
            st.session_state["wizard_page"] = "career_exploration"
            st.rerun()

    # ── Header ─────────────────────────────────────────────────
    st.title("Career Exploration — Income Analysis")
    if cip_code and cip_name:
        st.info(f"**CIP {cip_code}** — {cip_name}  |  Location: **{geo}**")
    st.caption(
        "Hourly wage data (Low / Median / High) for the top occupations. "
        "Data from Job Bank Canada (jobbank.gc.ca)."
    )

    if not top_nocs:
        st.warning("No occupation data available. Please go back and run the analysis first.")
        return

    # ── Fetch wages for all NOCs ──────────────────────────────
    all_wages = {}
    with st.spinner("Fetching wage data from Job Bank..."):
        for noc in top_nocs:
            all_wages[noc["code"]] = fetch_jobbank_wages(noc["code"], geo)

    has_data = any(w.get("wages") for w in all_wages.values())
    if not has_data:
        st.warning("Could not retrieve wage data from Job Bank for these occupations.")
        return

    # ── Wage Comparison Table ─────────────────────────────────
    st.header("Wage Comparison ($/hour)")
    st.caption(f"Hourly wages for the top occupations in **{geo}**.")

    # Build HTML table
    n_nocs = len(top_nocs)
    col_defs = (
        "<colgroup>"
        "<col style='width:200px;'/>"
        + "".join(f"<col style='width:{max(100, 500 // n_nocs)}px;'/>" for _ in range(n_nocs))
        + "</colgroup>"
    )

    # Header row
    header_cells = "<th style='text-align:left; padding:8px 10px; background:#F1F5F9; " \
                   "color:#334155; font-size:0.82rem; border-bottom:2px solid #CBD5E1;'>Occupation</th>"
    for noc in top_nocs:
        code = noc["code"]
        title = all_wages[code].get("title") or noc["name"].split(" ", 1)[-1] if " " in noc["name"] else code
        # Truncate long titles
        if len(title) > 25:
            title = title[:23] + "…"
        header_cells += (
            f"<th style='text-align:center; padding:8px 6px; background:#F1F5F9; "
            f"color:#334155; font-size:0.78rem; border-bottom:2px solid #CBD5E1;'>"
            f"<div style='font-weight:700;'>{code}</div>"
            f"<div style='font-weight:400; color:#64748B; font-size:0.72rem;'>{title}</div></th>"
        )

    # Wage color helper
    def _wage_cell(value):
        if value is None:
            return "<td style='text-align:center; padding:6px; color:#9CA3AF;'>—</td>"
        return (
            f"<td style='text-align:center; padding:6px; font-weight:600; "
            f"font-size:0.88rem; color:#1E293B;'>${value:.2f}</td>"
        )

    rows_html = ""
    for label, key in [("Low", "low"), ("Median", "median"), ("High", "high")]:
        # Row background colors
        if key == "low":
            bg = "#FEF2F2"
            label_color = "#9CA3AF"
        elif key == "median":
            bg = "#F0FDF4"
            label_color = "#16A34A"
        else:
            bg = "#EFF6FF"
            label_color = "#2563EB"

        row = (
            f"<tr style='background:{bg};'>"
            f"<td style='padding:8px 10px; font-weight:600; font-size:0.85rem; "
            f"color:{label_color};'>{label}</td>"
        )
        for noc in top_nocs:
            wages = all_wages[noc["code"]].get("wages", {})
            row += _wage_cell(wages.get(key))
        row += "</tr>"
        rows_html += row

    # Annual estimate row (median × 2080 hours)
    annual_row = (
        "<tr style='background:#FFF7ED; border-top:2px solid #CBD5E1;'>"
        "<td style='padding:8px 10px; font-weight:600; font-size:0.85rem; "
        "color:#EA580C;'>Est. Annual<br/><span style=\"font-size:0.7rem; font-weight:400; "
        "color:#94A3B8;\">(Median × 2,080 hrs)</span></td>"
    )
    for noc in top_nocs:
        wages = all_wages[noc["code"]].get("wages", {})
        med = wages.get("median")
        if med is not None:
            annual = med * 2080
            annual_row += (
                f"<td style='text-align:center; padding:6px; font-weight:700; "
                f"font-size:0.88rem; color:#EA580C;'>${annual:,.0f}</td>"
            )
        else:
            annual_row += "<td style='text-align:center; padding:6px; color:#9CA3AF;'>—</td>"
    annual_row += "</tr>"
    rows_html += annual_row

    table_html = (
        f"<table style='width:100%; border-collapse:collapse; table-layout:fixed; "
        f"border:1px solid #E2E8F0; border-radius:8px; overflow:hidden;'>"
        f"{col_defs}"
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # ── Community Breakdown (expandable) ──────────────────────
    # Show community breakdown for each NOC if available
    has_community = any(all_wages[n["code"]].get("community") for n in top_nocs)
    if has_community:
        st.divider()
        st.subheader("Regional Wage Breakdown")
        st.caption("Detailed wage data by community/region within the selected province.")

        for noc in top_nocs:
            community = all_wages[noc["code"]].get("community", [])
            if not community:
                continue
            with st.expander(f"{noc['name']}", expanded=False):
                comm_rows = ""
                for c in community:
                    comm_rows += (
                        f"<tr>"
                        f"<td style='padding:5px 8px; font-size:0.82rem; color:#334155;'>{c['area']}</td>"
                        f"<td style='text-align:center; padding:5px; font-size:0.82rem;'>${c['low']:.2f}</td>"
                        f"<td style='text-align:center; padding:5px; font-size:0.82rem; "
                        f"font-weight:600; color:#16A34A;'>${c['median']:.2f}</td>"
                        f"<td style='text-align:center; padding:5px; font-size:0.82rem;'>${c['high']:.2f}</td>"
                        f"</tr>"
                    )
                comm_table = (
                    "<table style='width:100%; border-collapse:collapse;'>"
                    "<thead><tr>"
                    "<th style='text-align:left; padding:5px 8px; font-size:0.78rem; "
                    "background:#F1F5F9; color:#64748B;'>Community</th>"
                    "<th style='text-align:center; padding:5px; font-size:0.78rem; "
                    "background:#F1F5F9; color:#64748B;'>Low</th>"
                    "<th style='text-align:center; padding:5px; font-size:0.78rem; "
                    "background:#F1F5F9; color:#64748B;'>Median</th>"
                    "<th style='text-align:center; padding:5px; font-size:0.78rem; "
                    "background:#F1F5F9; color:#64748B;'>High</th>"
                    "</tr></thead>"
                    f"<tbody>{comm_rows}</tbody></table>"
                )
                st.markdown(comm_table, unsafe_allow_html=True)

    # ── Quadrant Bubble Chart ─────────────────────────────────
    st.divider()
    st.header("Occupation Quadrant — Employment Count vs Income")
    st.caption(
        "Each bubble represents a specific occupation (5-digit NOC). "
        "X-axis: employment count (more people → further right). "
        "Y-axis: median income for age 25-64 (higher → more income). "
        "Bubble size: employment share (larger bubble = higher proportion of graduates)."
    )

    # Re-fetch NOC distribution for the quadrant chart
    noc_result = None
    try:
        with st.spinner("Querying occupation data for quadrant chart..."):
            noc_result = fetch_noc_distribution(cip_code, broad_field, education)
    except Exception:
        pass

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
                # Mark the top 5 NOCs with a distinct color
                top_codes = {n["code"] for n in top_nocs}
                st.plotly_chart(
                    noc_quadrant_bubble(
                        quadrant_data,
                        oasis_noc_set=top_codes,
                        highlight_label="Your Top 5 Occupations",
                    ),
                    use_container_width=True,
                )

                # Compact quadrant legend
                q1, q2, q3, q4 = st.columns(4)
                q1.markdown(
                    '<span style="color:#10B981;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Many + High Pay</span>',
                    unsafe_allow_html=True,
                )
                q2.markdown(
                    '<span style="color:#6366F1;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Few + High Pay</span>',
                    unsafe_allow_html=True,
                )
                q3.markdown(
                    '<span style="color:#F59E0B;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Many + Lower Pay</span>',
                    unsafe_allow_html=True,
                )
                q4.markdown(
                    '<span style="color:#F43F5E;font-size:1.2rem;">&#9679;</span> '
                    '<span style="font-size:0.82rem;">Few + Lower Pay</span>',
                    unsafe_allow_html=True,
                )
                st.caption("Bubble size = share of graduates. Blue bubbles = your top 5 occupations.")
            else:
                st.info("Could not retrieve income data for the occupation quadrant chart.")
        except Exception as e:
            st.error(f"Error loading quadrant data: {e}")
            st.code(traceback.format_exc())
    else:
        st.info("Occupation distribution data not available for the quadrant chart.")


# ── Router ────────────────────────────────────────────────────────


def main(default_page: str = "profile"):
    if "wizard_page" not in st.session_state:
        st.session_state["wizard_page"] = default_page

    page = st.session_state["wizard_page"]
    if page == "deep_analysis":
        render_deep_analysis_page()
    elif page == "cip_distribution":
        render_cip_distribution_page()
    elif page == "ce_analysis":
        render_ce_analysis_page()
    elif page == "ce_job_analysis":
        render_ce_job_analysis_page()
    elif page == "ce_skills":
        render_ce_skills_page()
    elif page == "ce_wages":
        render_ce_wages_page()
    elif page == "analysis":
        render_analysis_page()
    elif page == "career_exploration":
        render_career_exploration_page()
    else:
        render_profile_page()


if __name__ == "__main__":
    main()
