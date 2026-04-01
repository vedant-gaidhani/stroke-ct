import streamlit as st
import datetime
from app_utils import image_utils
from app_utils.image_utils import format_confidence
from app_utils import pdf_generator
from app_utils.cloudinary_utils import upload_to_cloudinary
from app_utils.email_utils import send_stroke_alert
from firebase_config import db
from firebase_utils import log_action

# ── MODEL LOADING ────────────────────────────────────────────────────────────
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

# Confidence threshold below which a "Normal" result is treated as suspicious
# and goes through the full segmentation review path
SUSPICIOUS_THRESHOLD = 0.75

# ── AUTH CHECK ────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.error("Please login from the main page to access this feature.")
    st.stop()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for key, default in [
    ("analysis_complete", False),
    ("analysis_data", {}),
    ("last_uploaded_file", None),
    ("cloudinary_errors", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title("📸 New Scan Analysis")
    st.markdown("Upload a brain CT scan for ischemic stroke detection and stroke lesion localisation.")
with col_badge:
    badge_color = "#10b981" if USING_REAL_MODELS else "#a78bfa"
    badge_label = "AI Models: Live" if USING_REAL_MODELS else "Demo Mode"
    st.markdown(
        f"""<div style='background:rgba({("16,185,129" if USING_REAL_MODELS else "167,139,250")},0.1);
            color:{badge_color};padding:8px 14px;border-radius:20px;text-align:center;
            font-weight:700;font-size:12px;margin-top:18px;
            border:1px solid rgba({("16,185,129" if USING_REAL_MODELS else "167,139,250")},0.2);
            backdrop-filter:blur(12px);display:flex;align-items:center;
            justify-content:center;gap:6px;letter-spacing:0.5px;text-transform:uppercase;'>
            <span style='width:6px;height:6px;border-radius:50%;background:{badge_color};
                         box-shadow:0 0 8px {badge_color};display:inline-block;'></span>
            {badge_label}
        </div>""",
        unsafe_allow_html=True
    )

# ── PATIENT DETAILS FORM ───────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    patient_name = st.text_input("Patient Name", placeholder="e.g., John Doe")
with col2:
    patient_id = st.text_input("Patient ID", placeholder="e.g., PT-2023-001")

col3, col4 = st.columns(2)
with col3:
    scan_date = st.date_input("Scan Date", datetime.date.today())
with col4:
    notes = st.text_area(
        "Clinical Notes",
        placeholder="Relevant history, onset time, or symptoms...",
        height=68
    )

st.markdown("---")

# ── FILE UPLOAD ────────────────────────────────────────────────────────────────
st.subheader("Upload CT Scan")
uploaded_file = st.file_uploader(
    "Choose an image or DICOM file",
    type=["png", "jpg", "jpeg", "dcm"],
    help="Supports PNG, JPG, and DICOM (.dcm) formats."
)

# Reset analysis on new file
if uploaded_file and st.session_state.get("last_uploaded_file") != uploaded_file.name:
    st.session_state["analysis_complete"] = False
    st.session_state["analysis_data"] = {}
    st.session_state["cloudinary_errors"] = []
    st.session_state["last_uploaded_file"] = uploaded_file.name

# ── ANALYSIS ───────────────────────────────────────────────────────────────────
if uploaded_file is not None:
    if st.button("🧠 Analyze Scan", type="primary", use_container_width=True):
        if not patient_name or not patient_id:
            st.error("Please enter both Patient Name and Patient ID to proceed.")
        else:
            with st.spinner("Running classification..."):
                try:
                    pil_image       = image_utils.load_image(uploaded_file)
                    processed_image = image_utils.preprocess_for_model(pil_image)

                    # ── STAGE 1: Classification (always runs) ─────────────────
                    label, confidence = predict_classification(processed_image)
                    triage_text, severity, bg_color = image_utils.get_triage(label, confidence)

                    # ── GATE: decide whether to proceed to Stage 2 ────────────
                    # Stroke-positive → always run seg + Grad-CAM
                    # Normal with low confidence → suspicious, run as review
                    # Normal with high confidence → skip seg and Grad-CAM
                    is_stroke     = (label == "Ischemic Stroke")
                    is_suspicious = (label == "Normal" and confidence < SUSPICIOUS_THRESHOLD)
                    run_localisation = is_stroke or is_suspicious

                    mask_array    = None
                    heatmap_array = None
                    fig           = None

                    if run_localisation:
                        # ── STAGE 2: Segmentation (gated) ─────────────────────
                        with st.spinner("Running stroke lesion segmentation..."):
                            mask_array = predict_segmentation(processed_image)

                        # ── STAGE 3: Grad-CAM (gated) ─────────────────────────
                        with st.spinner("Generating model attention map..."):
                            heatmap_array = generate_gradcam(processed_image)

                        fig = create_four_panel_figure(
                            processed_image, mask_array, heatmap_array
                        )

                    mask_present = (mask_array is not None and bool(mask_array.any()))

                    # ── STROKE ALERT EMAIL ────────────────────────────────────
                    if is_stroke and confidence > 0.80:
                        doctor_email = st.session_state.get("user_email", "")
                        doctor_name  = st.session_state.get("user_display_name", "Doctor")
                        if doctor_email:
                            sent = send_stroke_alert(
                                doctor_email=doctor_email,
                                doctor_name=doctor_name,
                                patient_name=patient_name,
                                patient_id=patient_id,
                                confidence=confidence,
                                scan_date=scan_date.isoformat(),
                            )
                            if sent:
                                st.toast(f"📧 Urgent alert sent to {doctor_email}", icon="📧")

                    # ── PDF REPORT ────────────────────────────────────────────
                    pdf_bytes = pdf_generator.generate_clinical_report(
                        patient_name=patient_name,
                        patient_id=patient_id,
                        scan_date=scan_date.isoformat(),
                        notes=notes,
                        label=label,
                        confidence=confidence,
                        triage_text=triage_text,
                        triage_color=bg_color,
                        original_image_pil=pil_image,
                        segmentation_fig=fig,          # None for normal high-conf
                        doctor_name=st.session_state.get("doctor_name", "Unknown"),
                        doctor_email=st.session_state.get("user_email", ""),
                        mask_present=mask_present,
                    )

                    # ── CLOUDINARY UPLOADS ────────────────────────────────────
                    image_url = ""
                    try:
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_url = upload_to_cloudinary(
                            image_utils.pil_to_bytes(pil_image),
                            filename=f"{st.session_state['user_uid']}_{patient_id}_{ts}.png",
                            folder="neurotriage/scans",
                        )
                    except Exception as img_err:
                        st.session_state["cloudinary_errors"].append(f"Image upload: {img_err}")

                    report_url = ""
                    try:
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        report_url = upload_to_cloudinary(
                            pdf_bytes,
                            filename=f"{patient_id}_{ts}.pdf",
                            folder=f"neurotriage/reports/{st.session_state['user_uid']}",
                        )
                    except Exception as pdf_err:
                        st.session_state["cloudinary_errors"].append(f"PDF upload: {pdf_err}")

                    # ── STORE IN SESSION ──────────────────────────────────────
                    st.session_state["analysis_data"] = {
                        "label":            label,
                        "confidence":       confidence,
                        "triage_text":      triage_text,
                        "severity":         severity,
                        "bg_color":         bg_color,
                        "is_stroke":        is_stroke,
                        "is_suspicious":    is_suspicious,
                        "run_localisation": run_localisation,
                        "fig":              fig,
                        "mask_present":     mask_present,
                        "pdf_bytes":        pdf_bytes,
                        "image_url":        image_url,
                        "report_url":       report_url,
                        "patient_name":     patient_name,
                        "patient_id":       patient_id,
                        "scan_date":        scan_date.isoformat(),
                        "notes":            notes,
                        "filename":         uploaded_file.name,
                    }
                    st.session_state["analysis_complete"] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # ── RESULTS PANEL ─────────────────────────────────────────────────────────
    if st.session_state["analysis_complete"]:
        for err in st.session_state.get("cloudinary_errors", []):
            st.warning(f"⚠️ {err}")

        data          = st.session_state["analysis_data"]
        is_stroke     = data["is_stroke"]
        is_suspicious = data["is_suspicious"]
        _accent       = "#E24B4A" if is_stroke else ("#EF9F27" if is_suspicious else "#1D9E75")
        _rgb          = "226,75,74" if is_stroke else ("239,159,39" if is_suspicious else "29,158,117")
        _border       = f"rgba({_rgb}, 0.25)"
        _bg           = f"rgba({_rgb}, 0.06)"

        st.markdown("---")

        # ── OUTPUT 1: Prediction ──────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="background:{_bg}; padding:1.75rem 2rem; border-radius:16px;
                        border:1px solid {_border}; margin-bottom:1rem;">
                <div style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;
                            letter-spacing:2px;margin-bottom:6px;font-weight:700;">Prediction</div>
                <div style="font-size:26px;font-weight:700;color:#fff;margin-bottom:14px;">
                    {data['label']}
                </div>
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                                border-radius:8px;padding:6px 14px;display:inline-flex;
                                align-items:center;gap:8px;">
                        <span style="font-size:10px;color:rgba(255,255,255,0.4);
                                     text-transform:uppercase;letter-spacing:1.5px;">Confidence</span>
                        <span style="font-size:18px;font-family:'Space Mono',monospace;
                                     color:#fff;font-weight:300;">
                            {format_confidence(data['confidence'])}
                        </span>
                    </div>
                    <div style="background:{_accent}22;border:1px solid {_border};border-radius:8px;
                                padding:6px 14px;display:inline-flex;align-items:center;gap:6px;">
                        <span style="width:6px;height:6px;border-radius:50%;background:{_accent};
                                     box-shadow:0 0 6px {_accent};"></span>
                        <span style="font-size:11px;color:{_accent};font-weight:700;
                                     text-transform:uppercase;letter-spacing:1px;">
                            {data['triage_text']}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Confidence quality warnings
        if data["confidence"] < 0.60:
            st.error("Very low confidence — do not rely on this prediction for clinical decisions.")
        elif 0.60 <= data["confidence"] < SUSPICIOUS_THRESHOLD:
            st.warning("Borderline confidence — review recommended before any clinical decision.")

        # ── NORMAL PATH: stop here (no lesion visuals) ────────────────────────
        if not data["run_localisation"]:
            st.markdown(
                """<div style="background:rgba(29,158,117,0.06);border:1px solid rgba(29,158,117,0.2);
                               border-radius:12px;padding:1rem 1.25rem;margin-top:1rem;
                               font-size:13px;color:rgba(255,255,255,0.5);">
                   No ischemic lesion localisation required for this scan.
                   Lesion overlay and Grad-CAM are not generated for normal high-confidence results.
                </div>""",
                unsafe_allow_html=True
            )

        # ── ABNORMAL PATH: show localisation outputs ───────────────────────────
        else:
            # ── OUTPUT 2: CT Analysis panels ─────────────────────────────────
            st.markdown(
                """<div style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;
                               letter-spacing:2px;font-weight:700;margin:1.5rem 0 0.5rem 0;">
                   CT Analysis Views
                </div>""",
                unsafe_allow_html=True
            )
            if data["fig"] is not None:
                st.pyplot(data["fig"])

            # ── Empty mask notice ─────────────────────────────────────────────
            if not data["mask_present"]:
                st.info(
                    "No confident lesion region detected for this scan. "
                    "Classification result and model attention map are shown above."
                )

            # ── Grad-CAM disclaimer ───────────────────────────────────────────
            st.markdown(
                """<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
                               border-radius:10px;padding:12px 16px;margin-top:0.25rem;
                               font-size:12px;color:rgba(255,255,255,0.4);line-height:1.5;">
                   <strong style="color:rgba(255,255,255,0.6);">Model Attention Map</strong>
                   shows where the model focused when making its prediction.
                   It is an explanation aid, not a precise lesion boundary.
                   Refer to the <strong style="color:rgba(255,255,255,0.6);">Lesion Overlay</strong>
                   for stroke region segmentation.
                </div>""",
                unsafe_allow_html=True
            )

        # ── OUTPUT FINAL: Save / Export (both paths) ──────────────────────────
        st.markdown("---")
        ac1, ac2 = st.columns(2)

        with ac1:
            st.download_button(
                label="📄 Download Report",
                data=data["pdf_bytes"],
                file_name=f"NeuroTriage_{data['patient_id']}_{data['scan_date']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_report_btn"
            )

        with ac2:
            if st.button(
                "💾 Save to Patient History",
                type="secondary",
                use_container_width=True,
                key="save_record_btn"
            ):
                try:
                    db.collection("scans").document().set({
                        "doctor_uid":     st.session_state["user_uid"],
                        "patient_name":   data["patient_name"],
                        "patient_id":     data["patient_id"],
                        "scan_date":      data["scan_date"],
                        "notes":          data["notes"],
                        "label":          data["label"],
                        "confidence":     float(data["confidence"]),
                        "triage_level":   data["severity"],
                        "triage_text":    data["triage_text"],
                        "timestamp":      datetime.datetime.now().isoformat(),
                        "image_filename": data["filename"],
                        "image_url":      data["image_url"],
                        "report_url":     data["report_url"],
                        "mask_present":   data["mask_present"],
                    })
                    log_action(
                        st.session_state["user_uid"],
                        "scan_saved",
                        patient_name=data["patient_name"],
                        details=f"Patient ID: {data['patient_id']}"
                    )
                    msg = f"Saved. [View PDF Report]({data['report_url']})" if data["report_url"] else "Saved to Patient History."
                    st.success(f"✅ {msg}")
                    st.session_state["analysis_complete"] = False
                    st.session_state["analysis_data"] = {}
                except Exception as e:
                    st.error(f"Failed to save: {e}")
