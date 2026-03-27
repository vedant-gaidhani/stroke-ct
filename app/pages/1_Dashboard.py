import streamlit as st
import datetime
from firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("🔒 Please login from the main page to access this feature.")
    st.stop()

# --- PAGE HEADER ---
doctor_name = st.session_state.get("doctor_name", "Doctor")
hour = datetime.datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
today_str = datetime.date.today().isoformat()

st.markdown(f"# 👋 {greeting}, Dr. {doctor_name}!")
st.caption(f"Here's your clinical dashboard for {datetime.date.today().strftime('%A, %B %d, %Y')}")
st.markdown("---")

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
total_scans = len(scans)
stroke_count = sum(1 for s in scans if s.get("label") == "Stroke")
normal_count = sum(1 for s in scans if s.get("label") == "Normal")
today_count = sum(1 for s in scans if s.get("scan_date") == today_str)

# --- METRIC CARDS ---
st.subheader("📈 Overview")

def metric_card(col, title, value, icon, border_color="#1D9E75"):
    col.markdown(
        f"""
        <div style="background-color:#112240; border:1px solid {border_color}; border-radius:10px; 
                    padding:22px 18px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.3);">
            <div style="font-size:30px; margin-bottom:6px;">{icon}</div>
            <div style="color:{border_color}; font-size:40px; font-weight:800; line-height:1;">{value}</div>
            <div style="color:#8FA3BF; font-size:12px; font-weight:600; letter-spacing:1px; margin-top:6px;">{title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

c1, c2, c3, c4 = st.columns(4)
metric_card(c1, "TOTAL SCANS",      total_scans,   "🧠", "#1D9E75")
metric_card(c2, "STROKE DETECTED",  stroke_count,  "🔴", "#E24B4A")
metric_card(c3, "NORMAL RESULTS",   normal_count,  "✅", "#1D9E75")
metric_card(c4, "TODAY'S SCANS",    today_count,   "📅", "#EF9F27")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# --- RECENT ACTIVITY TABLE ---
st.subheader("📋 Recent Activity")

if not scans:
    st.info("No scans recorded yet. Use **New Scan** to analyze your first case!")
else:
    recent = scans[:5]

    # Table header
    st.markdown(
        """
        <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:10px;
                    background:#0D1526; border-radius:8px 8px 0 0; padding:10px 16px;
                    color:#1D9E75; font-size:12px; font-weight:700; letter-spacing:0.5px;">
            <span>PATIENT NAME</span><span>RESULT</span><span>CONFIDENCE</span><span>DATE</span><span>ACTION</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    for i, scan in enumerate(recent):
        label      = scan.get("label", "N/A")
        confidence = scan.get("confidence", 0)
        p_name     = scan.get("patient_name", "N/A")
        p_id       = scan.get("patient_id", "N/A")
        scan_date  = scan.get("scan_date", "N/A")
        triage     = scan.get("triage_level", "normal")

        label_color = "#E24B4A" if triage == "critical" else ("#EF9F27" if triage == "warning" else "#1D9E75")
        row_bg = "#112240" if i % 2 == 0 else "#0E1C35"

        st.markdown(
            f"""
            <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:10px;
                        background:{row_bg}; padding:12px 16px; align-items:center;
                        border-left:3px solid {label_color}; margin-top:2px;">
                <span style="font-weight:600;">{p_name}<br>
                      <span style="color:#8FA3BF; font-size:11px;">ID: {p_id}</span></span>
                <span style="color:{label_color}; font-weight:700;">{label.upper()}</span>
                <span style="color:#F8F9FA;">{confidence*100:.1f}%</span>
                <span style="color:#8FA3BF; font-size:13px;">{scan_date}</span>
                <span></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:4px; background:#0D1526; border-radius:0 0 8px 8px;'></div>", unsafe_allow_html=True)

# --- QUICK ACTIONS ---
st.markdown("---")
st.subheader("⚡ Quick Actions")
if st.button("📸  New Scan", type="primary", use_container_width=False):
    st.switch_page("pages/2_New_Scan.py")
