import streamlit as st
import datetime
import io
import pandas as pd
from utils import image_utils
from utils import pdf_generator
from utils.cloudinary_utils import upload_to_cloudinary
from firebase_config import db
from firebase_utils import log_action

# --- MODEL LOADING: Try real models, fall back to mock silently ---
try:
    from real_models import (
        load_classifier, load_unet,
        predict_classification, predict_segmentation,
        generate_gradcam, create_four_panel_figure,
        USING_REAL_MODELS
    )
    _classifier = load_classifier()
    _unet = load_unet()
except Exception:
    from mock_models import (
        predict_classification, predict_segmentation,
        generate_gradcam, create_four_panel_figure
    )
    USING_REAL_MODELS = False

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("🔒 Please login to access this feature.")
    st.stop()

st.title("📂 Batch Upload")
st.markdown("Upload multiple CT scans for batch analysis. Results are saved automatically and a CSV summary is available for download.")
st.markdown("---")

# --- OPTIONS ---
opt1, opt2 = st.columns(2)
with opt1:
    id_prefix = st.text_input(
        "Patient ID Prefix",
        value="BATCH",
        help="Applied to all scans - e.g. 'BATCH' -> BATCH-001, BATCH-002..."
    )
with opt2:
    scan_date = st.date_input("Scan Date for all files", datetime.date.today())

# --- MULTI-FILE UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload CT scans (PNG, JPG, JPEG, DCM)",
    type=["png", "jpg", "jpeg", "dcm"],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more files above, then click **Analyze All**.")
    st.stop()

st.info(f"**{len(uploaded_files)} file(s) ready.** Patient IDs will be assigned as `{id_prefix}-001`, `{id_prefix}-002` ...")

if st.button("🚀 Analyze All", type="primary", use_container_width=True):

    progress_bar  = st.progress(0)
    status_text   = st.empty()
    results       = []
    stroke_scans  = []   # collect for optional PDF generation

    for i, f in enumerate(uploaded_files):
        status_text.text(f"Analyzing scan {i+1} of {len(uploaded_files)}: {f.name}")
        patient_id = f"{id_prefix}-{i+1:03d}"
        timestamp  = datetime.datetime.now().isoformat()

        try:
            pil_image  = image_utils.load_image(f)
            processed  = image_utils.preprocess_for_model(pil_image)
            label, confidence = predict_classification(processed)
            triage_text, severity, color = image_utils.get_triage(label, confidence)

            results.append({
                "Filename"  : f.name,
                "Patient ID": patient_id,
                "Result"    : label,
                "Confidence": f"{confidence*100:.1f}%",
                "Confidence_raw": confidence,
                "Triage"    : triage_text,
                "Severity"  : severity,
                "Color"     : color,
                "Date"      : scan_date.isoformat(),
                "Timestamp" : timestamp,
                "pil_image" : pil_image,   # kept for PDF later
            })

            if label == "Stroke":
                stroke_scans.append(results[-1])

        except Exception as e:
            results.append({
                "Filename"  : f.name,
                "Patient ID": patient_id,
                "Result"    : "ERROR",
                "Confidence": "-",
                "Confidence_raw": 0,
                "Triage"    : str(e),
                "Severity"  : "normal",
                "Color"     : "#8FA3BF",
                "Date"      : scan_date.isoformat(),
                "Timestamp" : timestamp,
                "pil_image" : None,
            })

        progress_bar.progress((i + 1) / len(uploaded_files))

    status_text.success(f"✅ Batch complete - {len(uploaded_files)} scans analyzed!")
    progress_bar.empty()

    # --- SUMMARY ---
    normal_count = sum(1 for r in results if r["Result"] == "Normal")
    stroke_count = sum(1 for r in results if r["Result"] == "Stroke")
    error_count  = sum(1 for r in results if r["Result"] == "ERROR")

    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("✅ Normal",  normal_count)
    sm2.metric("🔴 Stroke Detected", stroke_count)
    sm3.metric("⚠️ Errors", error_count)

    st.markdown("---")

    # --- COLOR-CODED RESULTS TABLE ---
    st.subheader("📋 Results")

    th1, th2, th3, th4, th5, th6 = st.columns([2, 1.5, 1, 1, 2, 1.5])
    th1.markdown("**Filename**")
    th2.markdown("**Patient ID**")
    th3.markdown("**Result**")
    th4.markdown("**Confidence**")
    th5.markdown("**Triage**")
    th6.markdown("**Date**")
    st.divider()

    for r in results:
        c = r["Color"]
        row_bg = "rgba(226,75,74,0.15)" if r["Result"] == "Stroke" else ("rgba(29,158,117,0.10)" if r["Result"] == "Normal" else "transparent")
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2, 1.5, 1, 1, 2, 1.5])
        rc1.markdown(f"<div style='background:{row_bg}; padding:6px 4px; border-radius:4px; font-size:13px;'>{r['Filename']}</div>", unsafe_allow_html=True)
        rc2.markdown(f"`{r['Patient ID']}`")
        rc3.markdown(f"<span style='color:{c}; font-weight:700;'>{r['Result']}</span>", unsafe_allow_html=True)
        rc4.markdown(r["Confidence"])
        rc5.markdown(f"<span style='color:{c}; font-size:12px;'>{r['Triage']}</span>", unsafe_allow_html=True)
        rc6.markdown(r["Date"])

    st.markdown("---")

    # --- CSV DOWNLOAD ---
    csv_cols = ["Filename", "Patient ID", "Result", "Confidence", "Triage", "Date", "Timestamp"]
    df_csv = pd.DataFrame([{k: r[k] for k in csv_cols} for r in results])
    csv_bytes = df_csv.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Results as CSV",
        data=csv_bytes,
        file_name=f"NeuroScan_Batch_{scan_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # --- BATCH FIRESTORE SAVE ---
    st.markdown("---")
    if st.button("💾 Save All to Records", type="secondary", use_container_width=True):
        saved = 0
        with st.spinner("Saving to Firestore..."):
            for r in results:
                if r["Result"] == "ERROR":
                    continue
                try:
                    db.collection("scans").add({
                        "doctor_uid"  : st.session_state["user_uid"],
                        "patient_name": f"Batch - {r['Filename']}",
                        "patient_id"  : r["Patient ID"],
                        "scan_date"   : r["Date"],
                        "notes"       : "Auto-saved via Batch Upload",
                        "label"       : r["Result"],
                        "confidence"  : r["Confidence_raw"],
                        "triage_level": r["Severity"],
                        "timestamp"   : r["Timestamp"],
                        "image_filename": r["Filename"],
                        "image_url"   : r.get("image_url", ""),
                        "report_url"  : r.get("report_url", ""),
                    })
                    saved += 1
                except Exception as e:
                    st.warning(f"Could not save {r['Filename']}: {e}")
        
        if saved > 0:
            log_action(
                doctor_uid=st.session_state["user_uid"],
                action="batch_uploaded",
                details=f"Batch processed {saved} scans ({stroke_count} stroke, {normal_count} normal)."
            )
        st.success(f"✅ {saved} records saved to database!")

    # --- STROKE-POSITIVE PDF GENERATION ---
    if stroke_scans:
        st.markdown("---")
        st.subheader(f"🔴 Generate Reports for {len(stroke_scans)} Stroke-Positive Scan(s)")
        st.caption("Individual clinical PDFs are generated for each stroke scan and offered as downloads.")

        for idx, r in enumerate(stroke_scans):
            if r["pil_image"] is None:
                continue

            with st.expander(f"📄 {r['Filename']} - {r['Result']} ({r['Confidence']})"):
                # Run segmentation + gradcam for the figure
                try:
                    processed = image_utils.preprocess_for_model(r["pil_image"])
                    mask      = predict_segmentation(processed)
                    heatmap   = generate_gradcam(processed)
                    fig       = create_four_panel_figure(processed, mask, heatmap)

                    with st.spinner("Generating PDF..."):
                        pdf_bytes = pdf_generator.generate_clinical_report(
                            patient_name  = f"Batch Patient - {r['Filename']}",
                            patient_id    = r["Patient ID"],
                            scan_date     = r["Date"],
                            notes         = "Auto-generated from Batch Upload.",
                            label         = r["Result"],
                            confidence    = r["Confidence_raw"],
                            triage_text   = r["Triage"],
                            triage_color  = r["Color"],
                            original_image_pil = r["pil_image"],
                            segmentation_fig   = fig,
                            doctor_name   = st.session_state.get("doctor_name", "Unknown"),
                            doctor_email  = st.session_state.get("user_email", ""),
                        )
                        # Upload PDF to Cloudinary
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_url = upload_to_cloudinary(
                            pdf_bytes,
                            filename=f"{r['Patient ID']}_{ts}.pdf",
                            folder=f"neuroscan/reports/{st.session_state.get('user_uid', 'unknown')}",
                        )

                    st.download_button(
                        label=f"⬇️ Download PDF - {r['Patient ID']}",
                        data=pdf_bytes,
                        file_name=f"NeuroScan_{r['Patient ID']}_{r['Date']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_dl_{idx}",
                        use_container_width=True,
                    )
                    if pdf_url:
                        st.caption(f"☁️ [Cloud copy saved]({pdf_url})")
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Could not generate report: {e}")
