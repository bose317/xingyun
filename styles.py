"""Global CSS styles for modern, professional UI."""

# Modern color palette
ACCENT = "#6366F1"       # Indigo
ACCENT_LIGHT = "#818CF8"
ACCENT_BG = "rgba(99, 102, 241, 0.08)"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"
BORDER = "#E2E8F0"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
GRADIENT = "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%)"

GLOBAL_CSS = """
<style>
/* ── Import modern font ──────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base overrides ──────────────────────────────────────── */
html {
    scroll-behavior: smooth;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Sidebar styling ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
}
section[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #F1F5F9 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.2) !important;
    transform: translateY(-1px);
}

/* ── Headers ─────────────────────────────────────────────── */
.stApp h1, .stApp h2, .stApp h3 {
    font-family: 'Inter', sans-serif !important;
    color: #1E293B;
}

/* ── Section fade-in animation ───────────────────────────── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}

.yf-section {
    animation: fadeSlideUp 0.6s ease-out both;
}

.yf-section:nth-child(2) { animation-delay: 0.1s; }
.yf-section:nth-child(3) { animation-delay: 0.2s; }
.yf-section:nth-child(4) { animation-delay: 0.3s; }

/* ── Metric cards ────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 20px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

div[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12), 0 1px 3px rgba(0,0,0,0.06);
    transform: translateY(-2px);
    border-color: #C7D2FE;
}

div[data-testid="stMetric"] label {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: #1E293B !important;
}

div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
}

/* ── Animated number count-up effect ─────────────────────── */
@keyframes countPulse {
    0% { opacity: 0; transform: scale(0.85); }
    60% { opacity: 1; transform: scale(1.02); }
    100% { transform: scale(1); }
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {
    animation: countPulse 0.5s ease-out both;
}

/* ── Chart containers ────────────────────────────────────── */
.stPlotlyChart {
    border-radius: 14px;
    overflow: hidden;
    transition: box-shadow 0.3s ease;
}

.stPlotlyChart:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

/* ── Card wrapper ────────────────────────────────────────── */
.yf-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    transition: box-shadow 0.3s ease;
}

.yf-card:hover {
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}

/* ── Header bar (glassmorphism) ──────────────────────────── */
#yf-header {
    position: fixed;
    top: 3.5rem;
    left: 22rem;
    right: 0;
    z-index: 999;
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    padding: 14px 28px 12px;
    border-bottom: 1px solid rgba(226, 232, 240, 0.6);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

#yf-header h1 {
    margin: 0 0 2px;
    font-size: 1.3rem;
    font-weight: 700;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.01em;
}

#yf-header .caption {
    margin: 0 0 10px;
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 400;
}

/* ── Navigation pills ────────────────────────────────────── */
#yf-header .nav {
    display: flex;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
}

#yf-header .nav a {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    background: #F1F5F9;
    color: #475569 !important;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}

#yf-header .nav a:hover {
    background: #E0E7FF;
    color: #4338CA !important;
    border-color: #C7D2FE;
    transform: translateY(-1px);
}

/* ── Scroll-margin for sections ──────────────────────────── */
[id^='sect-'], [id^='deep-'] {
    scroll-margin-top: 200px;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    padding: 12px 24px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.45) !important;
    transform: translateY(-2px);
}

/* ── Expanders ───────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #475569 !important;
    border-radius: 10px !important;
}

/* ── Alerts ──────────────────────────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 4px !important;
}

/* ── Dividers ────────────────────────────────────────────── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, #E2E8F0 20%, #E2E8F0 80%, transparent) !important;
    margin: 2rem 0 !important;
}

/* ── Deep Analysis CTA card ──────────────────────────────── */
.yf-cta {
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 50%, #FDF4FF 100%);
    border: 1px solid #E0E7FF;
    border-radius: 20px;
    padding: 32px;
    text-align: center;
    margin: 8px 0;
}

.yf-cta h3 {
    color: #4338CA;
    font-size: 1.3rem;
    margin-bottom: 8px;
}

.yf-cta p {
    color: #6366F1;
    font-size: 0.95rem;
    margin-bottom: 0;
}

/* ── Section headers with accent line ────────────────────── */
.stApp h2 {
    position: relative;
    padding-bottom: 10px;
}

.stApp h2::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 40px;
    height: 3px;
    background: linear-gradient(90deg, #6366F1, #A855F7);
    border-radius: 2px;
}

/* ── Spinner ─────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: #6366F1 !important;
}

/* ── Grade badge ─────────────────────────────────────────── */
.yf-grade {
    display: inline-block;
    width: 48px;
    height: 48px;
    line-height: 48px;
    text-align: center;
    border-radius: 12px;
    font-size: 1.4rem;
    font-weight: 700;
    color: white;
    margin-right: 12px;
}

.yf-grade-a { background: linear-gradient(135deg, #10B981, #059669); }
.yf-grade-b { background: linear-gradient(135deg, #22D3EE, #06B6D4); }
.yf-grade-c { background: linear-gradient(135deg, #FBBF24, #F59E0B); }
.yf-grade-d { background: linear-gradient(135deg, #FB923C, #F97316); }
.yf-grade-f { background: linear-gradient(135deg, #F87171, #EF4444); }

/* ── Footer ──────────────────────────────────────────────── */
.yf-footer {
    text-align: center;
    padding: 20px 0 10px;
    color: #94A3B8;
    font-size: 0.8rem;
}
</style>
"""
