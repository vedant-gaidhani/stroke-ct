import streamlit as st
import datetime
import io
import csv
from firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("🔒 Please login to access this feature.")
    st.stop()

doctor_uid = st.session_state.get("user_uid", "")

st.title("📊 Reports & Audit")
st.markdown("View saved clinical reports and review your account activity log.")
st.markdown("---")

tab1, tab2 = st.tabs(["📄 Saved Reports", "🔎 Audit Log"])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — SAVED REPORTS (Cloudinary URLs from Firestore)
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.subheader("📄 Saved Clinical Reports")
    st.markdown("All scans that have a generated PDF report stored in Cloudinary.")

    @st.cache_data(ttl=60)
    def fetch_reports(uid):
        try:
            docs = (
                db.collection("scans")
                .where(filter=FieldFilter("doctor_uid", "==", uid))
                .order_by("timestamp", direction="DESCENDING")
                .limit(500)
                .stream()
            )
            # Only return records that have a report_url (Cloudinary)
            return [d.to_dict() for d in docs if d.to_dict().get("report_url")]
        except Exception as e:
            st.error(f"Could not load reports: {e}")
            return []

    reports = fetch_reports(doctor_uid)

    if not reports:
        st.info("No saved reports found. Analyze a scan and download the PDF to generate one.")
    else:
        st.caption(f"**{len(reports)}** report(s) found.")
        st.markdown("")

        # Header row
        rh1, rh2, rh3, rh4, rh5 = st.columns([2.5, 1.5, 1, 1, 1.5])
        rh1.markdown("**Patient Name**")
        rh2.markdown("**Patient ID**")
        rh3.markdown("**Result**")
        rh4.markdown("**Date**")
        rh5.markdown("**Report**")
        st.divider()

        for i, rec in enumerate(reports):
            label      = rec.get("label", "N/A")
            report_url = rec.get("report_url", "")
            label_color = "#E24B4A" if label == "Ischemic Stroke" else "#1D9E75"

            rc1, rc2, rc3, rc4, rc5 = st.columns([2.5, 1.5, 1, 1, 1.5])
            rc1.markdown(f"**{rec.get('patient_name', 'N/A')}**")
            rc2.markdown(f"`{rec.get('patient_id', 'N/A')}`")
            rc3.markdown(f"<span style='color:{label_color}; font-weight:700;'>{label}</span>", unsafe_allow_html=True)
            rc4.markdown(rec.get("scan_date", "N/A"))

            with rc5:
                if report_url:
                    st.link_button("📄 View / Download", report_url, use_container_width=True)
                else:
                    st.caption("—")
            st.divider()

# ═══════════════════════════════════════════════════════════════
# TAB 2 — AUDIT LOG
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🔎 Account Audit Log")
    st.markdown("A full record of all actions performed under your account.")

    @st.cache_data(ttl=30)
    def fetch_audit_log(uid):
        try:
            docs = (
                db.collection("audit_logs")
                .where(filter=FieldFilter("doctor_uid", "==", uid))
                .order_by("timestamp", direction="DESCENDING")
                .limit(1000)
                .stream()
            )
            return [d.to_dict() for d in docs]
        except Exception as e:
            st.error(f"Could not load audit log: {e}")
            return []

    logs = fetch_audit_log(doctor_uid)

    # Summary metric
    col_total, col_export = st.columns([3, 1])
    with col_total:
        st.metric("Total Actions Logged", len(logs))
    with col_export:
        if logs:
            # Build CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["timestamp", "action", "patient_name", "details"])
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    "timestamp":    log.get("timestamp", ""),
                    "action":       log.get("action", ""),
                    "patient_name": log.get("patient_name", ""),
                    "details":      log.get("details", ""),
                })
            csv_data = output.getvalue().encode("utf-8")
            st.download_button(
                label="⬇️ Export CSV",
                data=csv_data,
                file_name=f"audit_log_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("")

    # Action label styling
    ACTION_COLORS = {
        "login":            "#1D9E75",
        "logout":           "#8FA3BF",
        "scan_analyzed":    "#1E6FB5",
        "pdf_downloaded":   "#7B61FF",
        "batch_uploaded":   "#EF9F27",
        "compare_scans":    "#2EC4B6",
    }
    ACTION_ICONS = {
        "login":            "🔑",
        "logout":           "🚪",
        "scan_analyzed":    "🧠",
        "pdf_downloaded":   "📄",
        "batch_uploaded":   "📦",
        "compare_scans":    "🔬",
    }

    if not logs:
        st.info("No audit log entries yet. Actions like login, scan analysis, and PDF downloads will appear here.")
    else:
        # Header
        lh1, lh2, lh3, lh4 = st.columns([1.5, 1.5, 2.5, 1.5])
        lh1.markdown("**Action**")
        lh2.markdown("**Patient**")
        lh3.markdown("**Details**")
        lh4.markdown("**Timestamp**")
        st.divider()

        for log in logs:
            action  = log.get("action", "unknown")
            patient = log.get("patient_name", "—")
            details = log.get("details", "—")
            ts_raw  = log.get("timestamp", "")

            # Format timestamp nicely
            try:
                ts = datetime.datetime.fromisoformat(ts_raw).strftime("%d %b %Y %H:%M")
            except Exception:
                ts = ts_raw[:16] if ts_raw else "—"

            color = ACTION_COLORS.get(action, "#8FA3BF")
            icon  = ACTION_ICONS.get(action, "📋")
            badge = f"<span style='background:{color}22; color:{color}; padding:3px 10px; border-radius:12px; font-weight:700; font-size:12px;'>{icon} {action.replace('_', ' ').upper()}</span>"

            lc1, lc2, lc3, lc4 = st.columns([1.5, 1.5, 2.5, 1.5])
            lc1.markdown(badge, unsafe_allow_html=True)
            lc2.markdown(f"{patient}")
            lc3.markdown(f"<span style='color:#8FA3BF; font-size:13px;'>{details}</span>", unsafe_allow_html=True)
            lc4.markdown(f"<span style='color:#8FA3BF; font-size:12px;'>{ts}</span>", unsafe_allow_html=True)
            st.divider()
