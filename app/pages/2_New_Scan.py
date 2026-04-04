import streamlit as st
import datetime
import numpy as np
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
    help="Supports PNG, JPG, and DICOM (.dcm) formats. 3D DICOM volumes supported."
)

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
            try:
                slices = image_utils.load_study_volume(uploaded_file)
                num_slices = len(slices)

                # Use the middle slice as the 'representative' scan for PDFs
                rep_index = max(0, num_slices // 2)
                pil_image = slices[rep_index]

                # ── STAGE 1: Classification (all slices) ─────────────────
                slice_results = []
                study_is_stroke = False

                with st.spinner(f"Running classification on {num_slices} slice(s)..."):
                    for idx, pil_slice in enumerate(slices):
                        processed_image = image_utils.preprocess_for_model(pil_slice)
                        label, confidence = predict_classification(processed_image)
                        triage_text, severity, bg_color = image_utils.get_triage(label, confidence)
                        
                        is_stroke = (label == "Ischemic Stroke")
                        is_suspicious = (label == "Normal" and confidence < SUSPICIOUS_THRESHOLD)
                        
                        if is_stroke:
                            study_is_stroke = True
                        
                        slice_results.append({
                            "idx": idx + 1,
                            "pil_image": pil_slice,
                            "processed": processed_image,
                            "label": label,
                            "confidence": confidence,
                            "confidence_display": format_confidence(confidence),
                            "triage_text": triage_text,
                            "severity": severity,
                            "bg_color": bg_color,
                            "is_stroke": is_stroke,
                            "is_suspicious": is_suspicious,
                            "mask_array": None,
                            "heatmap_array": None,
                            "fig": None,
                            "lesion_pixels": 0
                        })

                # Resolve Study-level Predictions
                if study_is_stroke:
                    study_label = "Ischemic Stroke"
                    stroke_confidences = [res["confidence"] for res in slice_results if res["label"] == "Ischemic Stroke"]
                    study_confidence = max(stroke_confidences)
                else:
                    study_label = "Normal"
                    normal_confidences = [res["confidence"] for res in slice_results if res["label"] == "Normal"]
                    study_confidence = min(normal_confidences) if normal_confidences else 1.0

                study_triage_text, study_triage_severity, study_bg_color = image_utils.get_triage(study_label, study_confidence)
                study_is_suspicious = (study_label == "Normal" and study_confidence < SUSPICIOUS_THRESHOLD)
                
                # We need localisation if the study has stroke or is suspicious
                run_localisation = study_is_stroke or study_is_suspicious

                total_lesion_pixels = 0
                slices_with_lesion = 0
                mask_present = False

                # ── STAGE 2 & 3: Segmentation & GradCAM ─────────────────
                if run_localisation:
                    with st.spinner(f"Running stroke lesion segmentation..."):
                        for res in slice_results:
                            if res["is_stroke"] or res["is_suspicious"]:
                                mask_array = predict_segmentation(res["processed"])
                                heatmap_array = generate_gradcam(res["processed"], filename=uploaded_file.name, mask_array=mask_array)
                                fig = create_four_panel_figure(res["processed"], mask_array, heatmap_array)
                                
                                res["mask_array"] = mask_array
                                res["heatmap_array"] = heatmap_array
                                res["fig"] = fig
                                
                                if mask_array is not None and np.any(mask_array > 0):
                                    mask_present = True
                                    pixels = int(np.sum(mask_array > 0))
                                    res["lesion_pixels"] = pixels
                                    total_lesion_pixels += pixels
                                    slices_with_lesion += 1
                
                # Determine extent label
                extent_label = "None"
                if slices_with_lesion > 0:
                    if total_lesion_pixels < 1000: extent_label = "Small"
                    elif total_lesion_pixels <= 5000: extent_label = "Moderate"
                    else: extent_label = "Large"

                # Pull the best figure for the PDF
                study_fig = None
                if mask_present:
                    best_res = max(slice_results, key=lambda x: x["lesion_pixels"])
                    study_fig = best_res["fig"]
                elif run_localisation:
                    study_fig = slice_results[rep_index]["fig"]

                # ── ALERT EMAIL ────────────────────────────────────
                if study_is_stroke and study_confidence > 0.80:
                    doctor_email = st.session_state.get("user_email", "")
                    doctor_name  = st.session_state.get("user_display_name", "Doctor")
                    if doctor_email:
                        sent = send_stroke_alert(
                            doctor_email=doctor_email,
                            doctor_name=doctor_name,
                            patient_name=patient_name,
                            patient_id=patient_id,
                            confidence=study_confidence,
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
                    label=study_label,
                    confidence=study_confidence,
                    triage_text=study_triage_text,
                    triage_color=study_bg_color,
                    original_image_pil=pil_image,
                    segmentation_fig=study_fig,
                    doctor_name=st.session_state.get("doctor_name", "Unknown"),
                    doctor_email=st.session_state.get("user_email", ""),
                    mask_present=mask_present,
                    lesion_burden=total_lesion_pixels,
                    extent_label=extent_label,
                    slices_with_lesion=slices_with_lesion
                )

                # ── CLOUDINARY UPLOADS ────────────────────────────────────
                image_url, report_url = "", ""
                try:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_url = upload_to_cloudinary(
                        image_utils.pil_to_bytes(pil_image),
                        filename=f"{st.session_state['user_uid']}_{patient_id}_{ts}.png",
                        folder="neurotriage/scans",
                    )
                except Exception as img_err:
                    st.session_state["cloudinary_errors"].append(str(img_err))

                try:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_url = upload_to_cloudinary(
                        pdf_bytes,
                        filename=f"{patient_id}_{ts}.pdf",
                        folder=f"neurotriage/reports/{st.session_state['user_uid']}",
                    )
                except Exception as pdf_err:
                    st.session_state["cloudinary_errors"].append(str(pdf_err))

                # ── SESSION STORAGE ──────────────────────────────────────
                st.session_state["analysis_data"] = {
                    "label":            study_label,
                    "confidence":       study_confidence,
                    "triage_text":      study_triage_text,
                    "severity":         study_triage_severity,
                    "bg_color":         study_bg_color,
                    "is_stroke":        study_is_stroke,
                    "is_suspicious":    study_is_suspicious,
                    "run_localisation": run_localisation,
                    "mask_present":     mask_present,
                    "total_lesion_pixels": total_lesion_pixels,
                    "slices_with_lesion": slices_with_lesion,
                    "extent_label":     extent_label,
                    "slice_results":    slice_results,
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

        if data["confidence"] < 0.60:
            st.error("Very low confidence — do not rely on this prediction for clinical decisions.")
        elif 0.60 <= data["confidence"] < SUSPICIOUS_THRESHOLD:
            st.warning("Borderline confidence — review recommended.")

        # ── NORMAL PATH: stop here ────────────────────────────────────────
        if not data["run_localisation"]:
            st.markdown(
                """<div style="background:rgba(29,158,117,0.06);border:1px solid rgba(29,158,117,0.2);
                               border-radius:12px;padding:1rem 1.25rem;margin-top:1rem;
                               font-size:13px;color:rgba(255,255,255,0.5);">
                   No ischemic lesion localisation required for this scan.
                   Lesion overlay and Model Attention Maps are not generated for normal high-confidence results.
                </div>""",
                unsafe_allow_html=True
            )

        # ── ABNORMAL PATH: Lesion Burden & Slice Review ───────────────────────────
        else:
            if data["mask_present"]:
                b1, b2, b3 = st.columns(3)
                b1.metric("Lesion Burden (Pixels)", data["total_lesion_pixels"])
                b2.metric("Estimated Extent", data["extent_label"])
                b3.metric("Slices with Lesion", data["slices_with_lesion"])
            else:
                st.info("No confident lesion region detected for this scan.")

            st.markdown(
                """<div style="font-size:10px;color:rgba(255,255,255,0.35);text-transform:uppercase;
                               letter-spacing:2px;font-weight:700;margin:1.5rem 0 0.5rem 0;">
                   Slice Review
                </div>""",
                unsafe_allow_html=True
            )
            
            slice_results = data["slice_results"]
            
            if len(slice_results) > 1:
                slice_idx = st.slider("Select Slice", 1, len(slice_results), 1)
            else:
                slice_idx = 1
                
            res = slice_results[slice_idx - 1]

            if res["fig"]:
                st.markdown(f"**Slice {res['idx']}** | {res['label']} ({res['confidence_display']}) | Lesion Pixels: {res['lesion_pixels']}")
                st.pyplot(res["fig"])
            else:
                st.markdown(f"**Slice {res['idx']}** | {res['label']} ({res['confidence_display']})")
                st.info("No localisation performed for this slice.")

            st.markdown(
                """<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
                               border-radius:10px;padding:12px 16px;margin-top:0.25rem;
                               font-size:12px;color:rgba(255,255,255,0.4);line-height:1.5;">
                   <strong style="color:rgba(255,255,255,0.6);">Model Attention Map</strong>
                   A secondary visual explanation of where the classifier focused.
                   It is an explanation aid, not a precise lesion boundary or segmentation.
                   Refer to the <strong style="color:rgba(255,255,255,0.6);">Lesion Overlay</strong>
                   for stroke region segmentation results.
                </div>""",
                unsafe_allow_html=True
            )

        # ── OUTPUT FINAL: Save / Export ─────────────────────────────────────
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
                if db is None:
                    st.error("❌ Firebase is not connected. Cannot save to Patient History. Check deployment secrets.")
                elif not st.session_state.get("user_uid"):
                    st.error("❌ Session expired. Please log out and log back in, then try saving again.")
                else:
                    try:
                        db.collection("scans").document().set({
                            "doctor_uid":     st.session_state.get("user_uid", ""),
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
                            "lesion_burden":   data["total_lesion_pixels"],
                            "extent_label":    data["extent_label"],
                            "slices_with_lesion": data["slices_with_lesion"],
                        })
                        log_action(
                            st.session_state.get("user_uid", ""),
                            "scan_saved",
                            patient_name=data["patient_name"],
                            details=f"Patient ID: {data['patient_id']}"
                        )
                        msg = f"Saved. [View PDF Report]({data['report_url']})" if data["report_url"] else "Saved to Patient History."
                        st.success(f"✅ {msg}")
                        st.session_state["analysis_complete"] = False
                        st.session_state["analysis_data"] = {}
                    except Exception as e:
                        st.error(f"❌ Failed to save: {e}")
