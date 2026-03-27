import streamlit as st
import datetime
from app_utils import image_utils
from app_utils import pdf_generator
from app_utils.cloudinary_utils import upload_to_cloudinary
from app_utils.email_utils import send_stroke_alert
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
    # If both models failed to load weights, real_models sets USING_REAL_MODELS=False
except Exception:
    from mock_models import (
        predict_classification, predict_segmentation,
        generate_gradcam, create_four_panel_figure
    )
    USING_REAL_MODELS = False


# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.error("Please login from the main page to access this feature.")
    st.stop()

# --- SESSION STATE INITIALIZATION ---
if "analysis_complete" not in st.session_state:
    st.session_state["analysis_complete"] = False
if "analysis_data" not in st.session_state:
    st.session_state["analysis_data"] = {}
if "last_uploaded_file" not in st.session_state:
    st.session_state["last_uploaded_file"] = None
if "cloudinary_errors" not in st.session_state:
    st.session_state["cloudinary_errors"] = []

# --- PAGE LAYOUT ---
# --- PAGE HEADER + AI STATUS BADGE ---
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title("📸 New Scan Analysis")
    st.markdown("Upload a patient CT scan for AI-powered stroke detection and hemorrhage segmentation.")
with col_badge:
    if USING_REAL_MODELS:
        st.markdown(
            "<div style='background:#1D9E75;color:white;padding:8px 14px;border-radius:20px;text-align:center;font-weight:700;font-size:13px;margin-top:18px;'>🟢 AI Models: LIVE</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background:#EF9F27;color:white;padding:8px 14px;border-radius:20px;text-align:center;font-weight:700;font-size:13px;margin-top:18px;'>🟡 Demo Mode</div>",
            unsafe_allow_html=True
        )

# --- INPUT FORM ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        patient_name = st.text_input("Patient Name", placeholder="e.g., John Doe")
    with col2:
        patient_id = st.text_input("Patient ID", placeholder="e.g., PT-2023-001")
        
    col3, col4 = st.columns(2)
    with col3:
        scan_date = st.date_input("Scan Date", datetime.date.today())
    with col4:
        notes = st.text_area("Clinical Notes", placeholder="Relevant medical history or symptoms...", height=68)

st.markdown("---")

# --- FILE UPLOAD ---
st.subheader("Upload CT Scan")
uploaded_file = st.file_uploader("Choose an image or DICOM file", type=['png', 'jpg', 'jpeg', 'dcm'])

# Reset analysis if a new file is uploaded
if uploaded_file and st.session_state.get("last_uploaded_file") != uploaded_file.name:
    st.session_state["analysis_complete"] = False
    st.session_state["analysis_data"] = {}
    st.session_state["cloudinary_errors"] = []
    st.session_state["last_uploaded_file"] = uploaded_file.name

# --- ANALYSIS SECTION ---
if uploaded_file is not None:
    # 1. Analyze Button
    if st.button("🧠 Analyze Scan", type="primary", use_container_width=True):
        if not patient_name or not patient_id:
            st.error("Please enter both Patient Name and Patient ID to proceed.")
        else:
            with st.spinner('Running AI analysis pipeline...'):
                try:
                    # Load and process
                    pil_image = image_utils.load_image(uploaded_file)
                    processed_image = image_utils.preprocess_for_model(pil_image)
                    
                    # Inference — routes to real or mock depending on USING_REAL_MODELS
                    label, confidence = predict_classification(processed_image)
                    mask_array = predict_segmentation(processed_image)
                    heatmap_array = generate_gradcam(processed_image)
                    
                    # Visualize
                    fig = create_four_panel_figure(processed_image, mask_array, heatmap_array)
                    triage_text, severity, bg_color = image_utils.get_triage(label, confidence)

                    # --- STROKE ALERT EMAIL ---
                    if label == 'Stroke' and confidence > 0.80:
                        doctor_email = st.session_state.get('user_email', '')
                        doctor_name = st.session_state.get('user_display_name', 'Doctor')
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
                                st.toast(f'📧 Email alert sent to {doctor_email}', icon='📧')

                    # Generate PDF
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
                        segmentation_fig=fig,
                        doctor_name=st.session_state.get("doctor_name", "Unknown"),
                        doctor_email=st.session_state.get("user_email", ""),
                    )

                    # Cloudinary Uploads
                    image_url = ""
                    try:
                        img_bytes = image_utils.pil_to_bytes(pil_image)
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_url = upload_to_cloudinary(
                            img_bytes,
                            filename=f"{st.session_state['user_uid']}_{patient_id}_{ts}.png",
                            folder="neuroscan/scans",
                        )
                    except Exception as img_err:
                        st.session_state["cloudinary_errors"].append(f"Image Upload: {str(img_err)}")

                    report_url = ""
                    try:
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        report_url = upload_to_cloudinary(
                            pdf_bytes,
                            filename=f"{patient_id}_{ts}.pdf",
                            folder=f"neuroscan/reports/{st.session_state['user_uid']}",
                        )
                    except Exception as upload_err:
                        st.session_state["cloudinary_errors"].append(f"PDF Upload: {str(upload_err)}")

                    # Store in Session State
                    st.session_state["analysis_data"] = {
                        "label": label,
                        "confidence": confidence,
                        "triage_text": triage_text,
                        "severity": severity,
                        "bg_color": bg_color,
                        "fig": fig,
                        "pdf_bytes": pdf_bytes,
                        "image_url": image_url,
                        "report_url": report_url,
                        "patient_name": patient_name,
                        "patient_id": patient_id,
                        "scan_date": scan_date.isoformat(),
                        "notes": notes,
                        "filename": uploaded_file.name
                    }
                    st.session_state["analysis_complete"] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred during image processing: {str(e)}")

    # 2. Display Results if Complete
    if st.session_state["analysis_complete"]:
        # Show any Cloudinary errors that occurred
        for err in st.session_state.get("cloudinary_errors", []):
            st.error(f"❌ {err}")

        data = st.session_state["analysis_data"]
        
        st.markdown("### Analysis Results")
        st.markdown(
            f"""
            <div style="background-color: {data['bg_color']}; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <h2 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">{data['triage_text']}</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 18px;">AI Confidence: {data['confidence']*100:.1f}%</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if 0.60 <= data['confidence'] < 0.80 and data['label'] == "Stroke":
             st.warning("⚠️ Low confidence - AI recommends radiologist review before clinical decision.")
        elif data['confidence'] < 0.60:
             st.error("❌ Extreme uncertainty - Do not rely on AI prediction.")
             
        st.pyplot(data['fig'])

        st.markdown("### Actions")
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            st.download_button(
                label="📄 Download Clinical Report (PDF)",
                data=data["pdf_bytes"],
                file_name=f"NeuroScan_{data['patient_name']}_{data['scan_date']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_report_btn"
            )
            
        with action_col2:
            if st.button("💾 Save to Records", type="secondary", use_container_width=True, key="save_record_btn"):
                try:
                    doc_ref = db.collection("scans").document()
                    ds_dict = {
                        "doctor_uid": st.session_state["user_uid"],
                        "patient_name": data["patient_name"],
                        "patient_id": data["patient_id"],
                        "scan_date": data["scan_date"],
                        "notes": data["notes"],
                        "label": data["label"],
                        "confidence": float(data["confidence"]),
                        "triage_level": data["severity"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "image_filename": data["filename"],
                        "image_url": data["image_url"],
                        "report_url": data["report_url"],
                    }
                    doc_ref.set(ds_dict)
                    if data["report_url"]:
                        st.success(f"✅ Record saved! [View Report]({data['report_url']})")
                    else:
                        st.success(f"✅ Record saved successfully!")
                    
                    # Clear state after saving to avoid double-saves
                    st.session_state["analysis_complete"] = False
                    st.session_state["analysis_data"] = {}
                except Exception as e:
                    st.error(f"Failed to save record: {str(e)}")

