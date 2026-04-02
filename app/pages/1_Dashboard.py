import streamlit as st
import datetime
from firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter
from app_utils.image_utils import format_confidence

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("🔒 Please login from the main page to access this feature.")
    st.stop()

# --- PAGE HEADER ---
doctor_name = st.session_state.get("doctor_name", "Doctor")
hour = datetime.datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
today_str = datetime.date.today().isoformat()

st.markdown(f"# {greeting}, Dr. {doctor_name}")
st.caption(f"Clinical dashboard · {datetime.date.today().strftime('%A, %B %d, %Y')}")

# --- LOAD SCANS FROM FIRESTORE ---
doctor_uid = st.session_state.get("user_uid", "")

with st.spinner("Loading your records..."):
    try:
        docs = (
            db.collection("scans")
            .where(filter=FieldFilter("doctor_uid", "==", doctor_uid))
            .order_by("timestamp", direction="DESCENDING")
            .limit(100)
            .stream()
        )
        scans = [d.to_dict() for d in docs]
    except Exception as e:
        st.error(f"Could not load records: {e}")
        scans = []

# --- COMPUTE METRICS ---
total_scans  = len(scans)
stroke_count = sum(1 for s in scans if s.get("label") == "Ischemic Stroke")
normal_count = sum(1 for s in scans if s.get("label") == "Normal")
today_count  = sum(1 for s in scans if s.get("scan_date") == today_str)

# --- GLASSMORPHIC METRIC CARDS ---
def premium_metric_card(col, title, value, accent_color, delay_ms):
    col.markdown(
        f"""
        <style>
        .metric-card-hover {{
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        .metric-card-hover:hover {{
            transform: translateY(-6px) scale(1.02) !important;
            border-color: rgba(255,255,255,0.1) !important;
            box-shadow: 0 20px 40px -15px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        }}
        </style>
        <div class="metric-card-hover" style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);border-radius:20px;padding:2rem 1.5rem;backdrop-filter:blur(20px);box-shadow:inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 32px rgba(0,0,0,0.3);animation:fadeInUp 0.6s ease-out {delay_ms}ms backwards;cursor:default;position:relative;overflow:hidden;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;"><div style="width:8px;height:8px;border-radius:50%;background:{accent_color};box-shadow:0 0 8px {accent_color};animation:breatheDot 2.5s ease-in-out infinite;"></div><div style="font-size:11px;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:2px;font-weight:700;">{title}</div></div><div style="font-family:'Space Mono',monospace;font-size:48px;font-weight:300;color:#fff;letter-spacing:-0.05em;line-height:1;">{value}</div></div>
        """,
        unsafe_allow_html=True
    )

c1, c2, c3, c4 = st.columns(4)
premium_metric_card(c1, "Total Scans",      total_scans,  "#00f2fe", 0)
premium_metric_card(c2, "Ischemic Stroke",  stroke_count, "#ff0844", 100)
premium_metric_card(c3, "Normal Results",   normal_count, "#10b981", 200)
premium_metric_card(c4, "Today's Scans",    today_count,  "#a78bfa", 300)

st.markdown("<br>", unsafe_allow_html=True)

# --- RECENT ACTIVITY TABLE ---
st.markdown("### Recent Activity")

if not scans:
    st.info("No scans recorded yet. Use **New Scan** to analyze your first case!")
else:
    recent = scans[:5]

    # Table header
    st.markdown(
        """<div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.03); border-radius:12px 12px 0 0; padding:14px 20px; color:rgba(255,255,255,0.4); font-size:11px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; border:1px solid rgba(255,255,255,0.04); border-bottom:none;"><span>PATIENT</span><span>RESULT</span><span>CONFIDENCE</span><span>DATE</span><span>STATUS</span></div>""",
        unsafe_allow_html=True
    )

    for i, scan in enumerate(recent):
        label      = scan.get("label", "N/A")
        confidence = scan.get("confidence", 0)
        p_name     = scan.get("patient_name", "N/A")
        p_id       = scan.get("patient_id", "N/A")
        scan_date  = scan.get("scan_date", "N/A")
        triage     = scan.get("triage_level", "normal")

        is_stroke  = triage == "critical"
        dot_color   = "#ff0844" if is_stroke else ("#EF9F27" if triage == "warning" else "#10b981")
        label_color = dot_color
        confidence_pct = format_confidence(confidence)

        st.markdown(
            f"""
            <style>
            .activity-row-hover {{
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }}
            .activity-row-hover:hover {{
                background: rgba(255,255,255,0.04) !important;
                transform: translateX(4px) !important;
            }}
            </style>
            <div class="activity-row-hover" style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,{'0.02' if i % 2 == 0 else '0.01'}); padding:16px 20px; align-items:center; border-left:1px solid rgba(255,255,255,0.04); border-right:1px solid rgba(255,255,255,0.04); {'border-bottom:1px solid rgba(255,255,255,0.04);' if i == len(recent)-1 else ''} animation: fadeInUp 0.5s ease-out {(i+1)*80}ms backwards;"><span style="font-weight:600;color:#fff;">{p_name}<br><span style="color:rgba(255,255,255,0.3); font-size:11px; font-family:'Space Mono',monospace;">ID: {p_id}</span></span><span style="display:flex;align-items:center;gap:6px;"><span style="width:6px;height:6px;border-radius:50%;background:{dot_color};box-shadow:0 0 6px {dot_color};"></span><span style="color:{label_color}; font-weight:700; font-size:13px;">{label.upper()}</span></span><span style="color:#fff; font-family:'Space Mono',monospace; font-weight:300;">{confidence_pct}</span><span style="color:rgba(255,255,255,0.4); font-size:13px; font-family:'Space Mono',monospace;">{scan_date}</span><span style="font-size:10px;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:1px;">Reviewed</span></div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("""<div style='height:4px; background:rgba(255,255,255,0.02); border-radius:0 0 12px 12px; border:1px solid rgba(255,255,255,0.04); border-top:none;'></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- QUICK ACTIONS ---
st.markdown("### Quick Actions")
qa1, qa2, qa3 = st.columns(3)
with qa1:
    if st.button("📸  New Scan", type="primary", use_container_width=True):
        st.switch_page("pages/2_New_Scan.py")
with qa2:
    if st.button("📁  Patient History", use_container_width=True):
        st.switch_page("pages/3_Patient_History.py")
with qa3:
    if st.button("📊  Reports", use_container_width=True):
        st.switch_page("pages/5_Reports.py")
