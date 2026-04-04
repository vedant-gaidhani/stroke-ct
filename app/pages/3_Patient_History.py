import streamlit as st
import datetime
from firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter
from app_utils.image_utils import format_confidence

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("🔒 Please login to access this feature.")
    st.stop()

st.title("📁 Patient History")
st.markdown("Browse, search, and review all previously analyzed CT scans.")
st.markdown("---")

# --- FETCH ALL SCANS ---
doctor_uid = st.session_state.get("user_uid", "")

def fetch_all_scans(uid):
    """Always fetches fresh from Firestore — no cache, so new saves appear immediately."""
    if db is None:
        st.error("❌ Firebase is not connected. Check deployment secrets.")
        return []
    if not uid:
        st.error("❌ Session error. Please log out and log back in.")
        return []
    try:
        docs = (
            db.collection("scans")
            .where(filter=FieldFilter("doctor_uid", "==", uid))
            .order_by("timestamp", direction="DESCENDING")
            .limit(500)
            .stream()
        )
        return [d.to_dict() for d in docs]
    except Exception as e:
        st.error(f"❌ Could not load records: {e}")
        return []

all_scans = fetch_all_scans(doctor_uid)

# Refresh button — force re-fetch after saving a new scan
if st.button("🔄 Refresh", help="Fetch the latest records from the database"):
    st.rerun()

if not all_scans:
    st.info("No scan records found. Analyze your first case in the **New Scan** page!")
    st.stop()

# --- SEARCH BAR ---
search_query = st.text_input(
    "🔍 Search",
    placeholder="Search by patient name or patient ID...",
    label_visibility="collapsed",
)

# --- FILTER ROW ---
f1, f2, f3, f4 = st.columns([1.5, 1.5, 1.5, 2])
with f1:
    filter_result = st.selectbox("Result", ["All", "Ischemic Stroke", "Normal"], label_visibility="visible")
with f2:
    filter_triage = st.selectbox("Severity", ["All", "Critical", "Warning", "Normal"], label_visibility="visible")
with f3:
    filter_conf = st.selectbox("Confidence", ["All", ">= 90%", ">= 75%", "< 75%"], label_visibility="visible")
with f4:
    use_date_range = st.checkbox("Filter by date range")
    if use_date_range:
        dc1, dc2 = st.columns(2)
        with dc1:
            date_from = st.date_input("From", datetime.date.today() - datetime.timedelta(days=30), label_visibility="collapsed")
        with dc2:
            date_to = st.date_input("To", datetime.date.today(), label_visibility="collapsed")
    else:
        date_from = None
        date_to = None

# --- APPLY FILTERS ---
filtered = all_scans

if search_query:
    q = search_query.lower()
    filtered = [s for s in filtered if
                q in s.get("patient_name", "").lower() or
                q in s.get("patient_id", "").lower()]

if filter_result != "All":
    filtered = [s for s in filtered if s.get("label") == filter_result]

if filter_triage != "All":
    filtered = [s for s in filtered if s.get("triage_level", "normal").lower() == filter_triage.lower()]

if filter_conf != "All":
    if filter_conf == ">= 90%":
        filtered = [s for s in filtered if s.get("confidence", 0) >= 0.90]
    elif filter_conf == ">= 75%":
        filtered = [s for s in filtered if s.get("confidence", 0) >= 0.75]
    elif filter_conf == "< 75%":
        filtered = [s for s in filtered if s.get("confidence", 0) < 0.75]

if use_date_range and date_from and date_to:
    filtered = [s for s in filtered if date_from.isoformat() <= s.get("scan_date", "") <= date_to.isoformat()]

# --- PAGINATION ---
PAGE_SIZE = 10
total = len(filtered)

if total == 0:
    st.warning("No scans match your filters.")
    st.stop()

total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
col_count, col_page = st.columns([3, 1])
with col_count:
    st.caption(f"Showing **{min(PAGE_SIZE, total)}** of **{total}** scans")
with col_page:
    page = st.number_input("Page Number", min_value=1, max_value=total_pages, value=1, step=1, label_visibility="visible")

start = (page - 1) * PAGE_SIZE
end = start + PAGE_SIZE
page_scans = filtered[start:end]

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# COMPARE SCANS STATE
# ─────────────────────────────────────────────────────────────
if "compare_selection" not in st.session_state:
    st.session_state["compare_selection"] = []

# Helper to toggle selection
def toggle_compare(scan):
    sel = st.session_state["compare_selection"]
    pid = scan.get("patient_id")
    # Check all selections share the same patient
    if any(s.get("patient_id") != pid for s in sel):
        st.session_state["compare_selection"] = [scan]
        st.toast("⚠️ Compare only supports scans from the same patient. Selection reset.", icon="⚠️")
        return
    key = (scan.get("patient_id"), scan.get("scan_date"), scan.get("timestamp"))
    existing_keys = [(s.get("patient_id"), s.get("scan_date"), s.get("timestamp")) for s in sel]
    if key in existing_keys:
        st.session_state["compare_selection"] = [s for s in sel if
            (s.get("patient_id"), s.get("scan_date"), s.get("timestamp")) != key]
    else:
        if len(sel) >= 2:
            st.toast("⚠️ You can only select 2 scans to compare. Deselect one first.", icon="⚠️")
        else:
            st.session_state["compare_selection"].append(scan)

# --- TABLE HEADER ---
h0, h1, h2, h3, h4, h5, h6, h7 = st.columns([0.4, 2, 1.5, 1, 1, 1, 1, 1.5])
h0.markdown("**☑**")
h1.markdown("**Patient**")
h2.markdown("**Patient ID**")
h3.markdown("**Prediction**")
h4.markdown("**Confidence**")
h5.markdown("**Triage**")
h6.markdown("**Date**")
h7.markdown("**Actions**")
st.divider()

# --- TABLE ROWS ---
for i, scan in enumerate(page_scans):
    label      = scan.get("label", "N/A")
    confidence = scan.get("confidence", 0)
    triage     = scan.get("triage_level", "normal")
    p_name     = scan.get("patient_name", "N/A")
    p_id       = scan.get("patient_id", "N/A")
    scan_date  = scan.get("scan_date", "N/A")
    notes      = scan.get("notes", "No notes provided.")
    report_url = scan.get("report_url", "")

    label_color = "#E24B4A" if triage == "critical" else ("#EF9F27" if triage == "warning" else "#1D9E75")

    # Check if this row is selected
    sel_keys = [(s.get("patient_id"), s.get("scan_date"), s.get("timestamp")) for s in st.session_state["compare_selection"]]
    is_selected = (p_id, scan_date, scan.get("timestamp")) in sel_keys

    c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([0.4, 2, 1.5, 1, 1, 1, 1, 1.5])

    with c0:
        cb = st.checkbox("Select scan", value=is_selected, key=f"cmp_{start}_{i}", label_visibility="collapsed")
        if cb != is_selected:
            toggle_compare(scan)
            st.rerun()

    c1.markdown(f"**{p_name}**")
    c2.markdown(f"`{p_id}`")
    c3.markdown(f"<span style='color:{label_color}; font-weight:700;'>{label}</span>", unsafe_allow_html=True)
    c4.markdown(format_confidence(confidence))
    c5.markdown(f"<span style='color:{label_color};'>{triage.upper()}</span>", unsafe_allow_html=True)
    c6.markdown(f"{scan_date}")

    with c7:
        if st.button("🔍 Details", key=f"view_{start}_{i}", use_container_width=True):
            st.session_state[f"show_details_{start}_{i}"] = not st.session_state.get(f"show_details_{start}_{i}", False)

    # View Details expandable section
    if st.session_state.get(f"show_details_{start}_{i}", False):
        with st.container():
            st.markdown(
                f"""<div style="background:#112240; border-left:4px solid {label_color}; border-radius:6px; padding:16px; margin:4px 0 12px 0;">""",
                unsafe_allow_html=True
            )
            d1, d2, d3 = st.columns(3)
            d1.metric("Result", label)
            d2.metric("Confidence", format_confidence(confidence))
            d3.metric("Triage Level", triage.upper())

            st.markdown(f"**📅 Scan Date:** {scan_date}")
            st.markdown(f"**🆔 Patient ID:** {p_id}")
            st.markdown(f"**📝 Clinical Notes:** {notes}")

            st.markdown("---")
            asset_col1, asset_col2 = st.columns(2)

            with asset_col1:
                image_url = scan.get("image_url", "")
                if image_url:
                    st.image(image_url, caption="CT Scan Image", use_container_width=True)
                else:
                    st.caption("No image available in cloud.")

            with asset_col2:
                if report_url:
                    st.success("✅ Clinical Report Ready")
                    st.link_button("📄 View PDF Report", report_url, use_container_width=True)
                else:
                    st.warning("⚠️ No PDF report found for this record.")

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

# --- COMPARE BUTTON ---
sel = st.session_state["compare_selection"]
num_selected = len(sel)

if num_selected > 0:
    cmp_col1, cmp_col2 = st.columns([3, 1])
    with cmp_col1:
        st.info(f"📋 {num_selected}/2 scan(s) selected for comparison. Select exactly 2 to compare.")
    with cmp_col2:
        if st.button("❌ Clear Selection", use_container_width=True):
            st.session_state["compare_selection"] = []
            st.rerun()

if num_selected == 2:
    if st.button("🔬 Compare Selected Scans", type="primary", use_container_width=True):
        st.session_state["show_compare"] = True

# ─────────────────────────────────────────────────────────────
# COMPARISON PANEL
# ─────────────────────────────────────────────────────────────
if st.session_state.get("show_compare") and num_selected == 2:
    s1, s2 = sorted(sel, key=lambda s: s.get("scan_date", ""))  # oldest first

    l1 = s1.get("label", "N/A")
    l2 = s2.get("label", "N/A")
    c1v = s1.get("confidence", 0)
    c2v = s2.get("confidence", 0)
    d1 = s1.get("scan_date", "N/A")
    d2 = s2.get("scan_date", "N/A")

    # Progression logic
    if l1 == l2:
        prog_color = "#8FA3BF"
        prog_icon  = "➡️"
        prog_msg   = f"No change detected — both scans show **{l1}**."
    elif l1 == "Ischemic Stroke" and l2 == "Normal":
        prog_color = "#1D9E75"
        prog_icon  = "📈"
        prog_msg   = f"Patient status **improved** from **Ischemic Stroke** → **Normal** between {d1} and {d2}."
    else:  # Normal → Ischemic Stroke
        prog_color = "#E24B4A"
        prog_icon  = "📉"
        prog_msg   = f"Patient status **deteriorated** from **Normal** → **Ischemic Stroke** between {d1} and {d2}."

    st.markdown("---")
    st.subheader("🔬 Scan Comparison")

    # Progression summary banner
    st.markdown(
        f"""<div style="background:{prog_color}22; border-left:5px solid {prog_color}; border-radius:8px;
            padding:16px 20px; margin-bottom:20px; font-size:15px; color:{prog_color}; font-weight:600;">
            {prog_icon} {prog_msg}
        </div>""",
        unsafe_allow_html=True,
    )

    # Side-by-side comparison columns
    col_left, col_sep, col_right = st.columns([5, 0.1, 5])

    def render_scan_panel(col, scan, label_str, side_label):
        lbl   = scan.get("label", "N/A")
        conf  = scan.get("confidence", 0)
        date  = scan.get("scan_date", "N/A")
        triage = scan.get("triage_level", "normal")
        lc    = "#E24B4A" if lbl == "Ischemic Stroke" else "#1D9E75"

        with col:
            st.markdown(
                f"<div style='text-align:center; font-size:13px; color:#8FA3BF; font-weight:600; margin-bottom:8px;'>{side_label}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='background:#112240; border-radius:10px; padding:16px; border:1px solid {lc}44;'>",
                unsafe_allow_html=True
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Date",       date)
            m2.metric("Prediction",  lbl)
            m3.metric("Confidence",  format_confidence(conf))

            img_url = scan.get("image_url", "")
            if img_url:
                st.image(img_url, caption=f"Analysis Image — {date}", use_container_width=True)
            else:
                st.markdown(
                    "<div style='background:#0A0F1E; border-radius:6px; height:200px; display:flex; align-items:center; justify-content:center; color:#555;'>No image available</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

    render_scan_panel(col_left,  s1, l1, f"📅 Scan 1 — {d1} (Earlier)")
    with col_sep:
        st.markdown("<div style='border-left:2px solid #1D3557; height:100%; min-height:300px; margin-top:40px;'></div>", unsafe_allow_html=True)
    render_scan_panel(col_right, s2, l2, f"📅 Scan 2 — {d2} (Later)")

    if st.button("✖️ Close Comparison", use_container_width=True):
        st.session_state["show_compare"] = False
        st.rerun()

# --- PAGE NAVIGATION FOOTER ---
st.markdown("---")
nav1, nav2, nav3 = st.columns([1, 2, 1])
with nav1:
    if page > 1:
        if st.button("← Previous", use_container_width=True):
            st.session_state["_page"] = page - 1
with nav2:
    st.markdown(f"<div style='text-align:center; color:#8FA3BF; padding-top:6px;'>Page {page} of {total_pages}</div>", unsafe_allow_html=True)
with nav3:
    if page < total_pages:
        if st.button("Next →", use_container_width=True):
            st.session_state["_page"] = page + 1
