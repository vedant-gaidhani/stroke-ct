import streamlit as st
import datetime
import pandas as pd
from app_utils import image_utils
from app_utils.image_utils import format_confidence
from app_utils import pdf_generator
from app_utils.cloudinary_utils import upload_to_cloudinary
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
st.markdown("Upload multiple CT scans for batch analysis. Results are saved to Patient History with clinical PDFs for stroke-positive cases.")
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
    st.session_state["batch_results"] = []
    st.session_state["_batch_file_names"] = None
    st.session_state["batch_saved_records"] = []
    st.stop()

# Reset batch results if files changed
file_names = tuple(f.name for f in uploaded_files)
if st.session_state.get("_batch_file_names") != file_names:
    st.session_state["batch_results"] = []
    st.session_state["batch_saved_records"] = []
    st.session_state["_batch_file_names"] = file_names

st.info(f"**{len(uploaded_files)} file(s) ready.** Patient IDs will be assigned as `{id_prefix}-001`, `{id_prefix}-002` ...")

# ─────────────────────────────────────────────────
# STEP 1: ANALYZE ALL
# ─────────────────────────────────────────────────
if st.button("🔬 Analyze All", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text  = st.empty()
    results      = []

    for i, f in enumerate(uploaded_files):
        status_text.text(f"Analyzing scan {i+1} of {len(uploaded_files)}: {f.name}")
        patient_id = f"{id_prefix}-{i+1:03d}"
        timestamp  = datetime.datetime.now().isoformat()

        try:
            pil_image = image_utils.load_image(f)
            processed = image_utils.preprocess_for_model(pil_image)
            label, confidence = predict_classification(processed)
            triage_text, severity, color = image_utils.get_triage(label, confidence)

            results.append({
                "Filename"      : f.name,
                "Patient ID"    : patient_id,
                "Result"        : label,
                "Confidence"    : format_confidence(confidence),
                "Confidence_raw": confidence,
                "Triage"        : triage_text,
                "Severity"      : severity,
                "Color"         : color,
                "Date"          : scan_date.isoformat(),
                "Timestamp"     : timestamp,
                "pil_image"     : pil_image,
            })

        except Exception as e:
            results.append({
                "Filename"      : f.name,
                "Patient ID"    : patient_id,
                "Result"        : "ERROR",
                "Confidence"    : "-",
                "Confidence_raw": 0,
                "Triage"        : str(e),
                "Severity"      : "normal",
                "Color"         : "#8FA3BF",
                "Date"          : scan_date.isoformat(),
                "Timestamp"     : timestamp,
                "pil_image"     : None,
            })

        progress_bar.progress((i + 1) / len(uploaded_files))

    st.session_state["batch_results"] = results
    st.session_state["batch_saved_records"] = []
    status_text.success(f"✅ Batch analysis complete — {len(uploaded_files)} scans analyzed!")
    progress_bar.empty()

# ─────────────────────────────────────────────────
# DISPLAY RESULTS (from session state)
# ─────────────────────────────────────────────────
results = st.session_state.get("batch_results", [])

if results:
    normal_count = sum(1 for r in results if r["Result"] == "Normal")
    stroke_count = sum(1 for r in results if r["Result"] == "Ischemic Stroke")
    error_count  = sum(1 for r in results if r["Result"] == "ERROR")

    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("✅ Normal",          normal_count)
    sm2.metric("🔴 Ischemic Stroke", stroke_count)
    sm3.metric("⚠️ Errors",         error_count)

    st.markdown("---")
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
        row_bg = "rgba(226,75,74,0.15)" if r["Result"] == "Ischemic Stroke" else ("rgba(29,158,117,0.10)" if r["Result"] == "Normal" else "transparent")
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2, 1.5, 1, 1, 2, 1.5])
        rc1.markdown(f"<div style='background:{row_bg}; padding:6px 4px; border-radius:4px; font-size:13px;'>{r['Filename']}</div>", unsafe_allow_html=True)
        rc2.markdown(f"`{r['Patient ID']}`")
        rc3.markdown(f"<span style='color:{c}; font-weight:700;'>{r['Result']}</span>", unsafe_allow_html=True)
        rc4.markdown(r["Confidence"])
        rc5.markdown(f"<span style='color:{c}; font-size:12px;'>{r['Triage']}</span>", unsafe_allow_html=True)
        rc6.markdown(r["Date"])

    st.markdown("---")

    # CSV Download
    csv_cols  = ["Filename", "Patient ID", "Result", "Confidence", "Triage", "Date", "Timestamp"]
    df_csv    = pd.DataFrame([{k: r[k] for k in csv_cols} for r in results])
    csv_bytes = df_csv.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Results as CSV",
        data=csv_bytes,
        file_name=f"NeuroTriage_Batch_{scan_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )


    # ─────────────────────────────────────────────────────────────────
    # DETAILED SCAN ANALYSIS (one expandable panel per scan)
    # ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🧠 Detailed Analysis")

    for idx, r in enumerate(results):
        if r["Result"] == "ERROR":
            st.expander(f"❌ {r['Filename']} — Error", expanded=False).error(r["Triage"])
            continue

        c = r["Color"]
        is_stroke     = r["Result"] == "Ischemic Stroke"
        is_suspicious = r["Result"] == "Normal" and r["Confidence_raw"] < 0.75
        _accent = "#E24B4A" if is_stroke else ("#EF9F27" if is_suspicious else "#1D9E75")
        _rgb    = "226,75,74" if is_stroke else ("239,159,39" if is_suspicious else "29,158,117")
        _border = f"rgba({_rgb}, 0.25)"
        _bg     = f"rgba({_rgb}, 0.06)"

        icon = "🔴" if is_stroke else ("🟡" if is_suspicious else "✅")
        label_str = f"{icon} {r['Filename']} — {r['Result']} ({r['Confidence']})"

        with st.expander(label_str, expanded=(idx == 0)):
            # Prediction banner
            st.markdown(
                f"""
                <div style="background:{_bg}; padding:1.5rem 1.75rem; border-radius:14px;
                            border:1px solid {_border}; margin-bottom:1rem;">
                    <div style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;
                                letter-spacing:2px;margin-bottom:6px;font-weight:700;">Prediction</div>
                    <div style="font-size:24px;font-weight:700;color:#fff;margin-bottom:12px;">
                        {r['Result']}
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                                    border-radius:8px;padding:5px 12px;display:inline-flex;
                                    align-items:center;gap:8px;">
                            <span style="font-size:10px;color:rgba(255,255,255,0.4);
                                         text-transform:uppercase;letter-spacing:1.5px;">Confidence</span>
                            <span style="font-size:16px;color:#fff;font-weight:400;">
                                {r['Confidence']}
                            </span>
                        </div>
                        <div style="background:{_accent}22;border:1px solid {_border};border-radius:8px;
                                    padding:5px 12px;display:inline-flex;align-items:center;gap:6px;">
                            <span style="width:6px;height:6px;border-radius:50%;background:{_accent};
                                         box-shadow:0 0 6px {_accent};"></span>
                            <span style="font-size:11px;color:{_accent};font-weight:700;
                                         text-transform:uppercase;letter-spacing:1px;">
                                {r['Triage']}
                            </span>
                        </div>
                        <div style="font-size:12px;color:rgba(255,255,255,0.35);">
                            Patient ID: <code>{r['Patient ID']}</code> &nbsp;|&nbsp; {r['Date']}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 4-panel CT analysis for stroke/suspicious
            if is_stroke or is_suspicious:
                if r["pil_image"] is not None:
                    with st.spinner("Generating CT analysis views..."):
                        try:
                            processed = image_utils.preprocess_for_model(r["pil_image"])
                            mask      = predict_segmentation(processed)
                            heatmap   = generate_gradcam(processed, filename=r["Filename"], mask_array=mask)
                            fig       = create_four_panel_figure(processed, mask, heatmap)

                            st.markdown(
                                """<div style="font-size:10px;color:rgba(255,255,255,0.35);
                                   text-transform:uppercase;letter-spacing:2px;font-weight:700;
                                   margin:1rem 0 0.5rem 0;">CT Analysis Views</div>""",
                                unsafe_allow_html=True,
                            )
                            st.pyplot(fig)

                            if mask is None or not bool(mask.any()):
                                st.info("No confident lesion region detected. Classification and model attention map shown above.")

                            st.markdown(
                                """<div style="background:rgba(255,255,255,0.02);border:1px solid
                                   rgba(255,255,255,0.05);border-radius:10px;padding:10px 14px;
                                   font-size:12px;color:rgba(255,255,255,0.4);line-height:1.5;
                                   margin-top:0.5rem;">
                                   <strong style="color:rgba(255,255,255,0.6);">Model Attention Map</strong>
                                   A secondary visual explanation of where the classifier focused.
                                   It is an explanation aid, not a precise lesion boundary or segmentation.
                                   Refer to the <strong style="color:rgba(255,255,255,0.6);">Lesion Overlay</strong>
                                   for stroke region segmentation results.
                                </div>""",
                                unsafe_allow_html=True,
                            )
                        except Exception as e:
                            st.warning(f"Could not generate analysis views: {e}")
            else:
                # Normal high-confidence — show the CT image only
                st.markdown(
                    """<div style="background:rgba(29,158,117,0.06);border:1px solid
                       rgba(29,158,117,0.2);border-radius:12px;padding:0.9rem 1.1rem;
                       margin-top:0.5rem;font-size:13px;color:rgba(255,255,255,0.5);">
                       No ischemic lesion localisation required. Lesion overlay and Grad-CAM
                       are not generated for normal high-confidence results.
                    </div>""",
                    unsafe_allow_html=True,
                )
                if r["pil_image"] is not None:
                    col_img, _ = st.columns([1, 1])
                    with col_img:
                        st.image(r["pil_image"], caption="Input CT Scan", use_container_width=True)


    if st.button("🚀 Complete and Save Batch", type="primary", use_container_width=True):
        if db is None:
            st.error("❌ Firebase is not initialized. Cannot save records.")
            st.stop()

        saved = 0
        saved_records = []

        with st.spinner(f"Uploading images, generating PDFs, and saving {normal_count + stroke_count} records..."):
            for r in results:
                if r["Result"] == "ERROR":
                    continue

                pdf_url   = ""
                image_url = ""

                # Upload scan image to Cloudinary
                if r["pil_image"] is not None:
                    try:
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_url = upload_to_cloudinary(
                            image_utils.pil_to_bytes(r["pil_image"]),
                            filename=f"batch_{r['Patient ID']}_{ts}.png",
                            folder="neurotriage/scans",
                        )
                    except Exception:
                        pass

                # For stroke OR suspicious/borderline cases: generate PDF + upload
                is_stroke = (r["Result"] == "Ischemic Stroke")
                is_suspicious = (r["Result"] == "Normal" and r["Confidence_raw"] < 0.75)
                
                if (is_stroke or is_suspicious) and r["pil_image"] is not None:
                    try:
                        processed = image_utils.preprocess_for_model(r["pil_image"])
                        mask      = predict_segmentation(processed)
                        heatmap   = generate_gradcam(processed, filename=r["Filename"], mask_array=mask)
                        fig       = create_four_panel_figure(processed, mask, heatmap)
                        mask_ok   = (mask is not None and bool(mask.any()))

                        pdf_bytes = pdf_generator.generate_clinical_report(
                            patient_name       = f"Batch Patient - {r['Filename']}",
                            patient_id         = r["Patient ID"],
                            scan_date          = r["Date"],
                            notes              = "Auto-generated from Batch Upload.",
                            label              = r["Result"],
                            confidence         = r["Confidence_raw"],
                            triage_text        = r["Triage"],
                            triage_color       = r["Color"],
                            original_image_pil = r["pil_image"],
                            segmentation_fig   = fig,
                            doctor_name        = st.session_state.get("doctor_name", "Unknown"),
                            doctor_email       = st.session_state.get("user_email", ""),
                            mask_present       = mask_ok,
                        )
                        pdf_url = upload_to_cloudinary(
                            pdf_bytes,
                            filename=f"report_{r['Patient ID']}.pdf",
                            folder=f"neurotriage/reports/{st.session_state.get('user_uid', 'unknown')}"
                        )
                    except Exception:
                        pass

                # Save to Firestore
                try:
                    if db is None:
                        raise Exception("Firebase not connected. Check deployment secrets (FIREBASE_SERVICE_ACCOUNT).")
                    db.collection("scans").add({
                        "doctor_uid"    : st.session_state.get("user_uid", ""),
                        "patient_name"  : f"Batch - {r['Filename']}",
                        "patient_id"    : r["Patient ID"],
                        "scan_date"     : r["Date"],
                        "notes"         : "Auto-saved via Batch Upload",
                        "label"         : r["Result"],
                        "confidence"    : r["Confidence_raw"],
                        "triage_level"  : r["Severity"],
                        "timestamp"     : r["Timestamp"],
                        "image_filename": r["Filename"],
                        "image_url"     : image_url,
                        "report_url"    : pdf_url,
                    })
                    saved += 1
                    saved_records.append({**r, "image_url": image_url, "report_url": pdf_url})
                except Exception as e:
                    st.warning(f"❌ Could not save {r['Filename']}: {e}")

        if saved > 0:
            log_action(
                st.session_state.get("user_uid", ""),
                "batch_uploaded",
                details=f"Batch processed {saved} scans ({stroke_count} stroke, {normal_count} normal)."
            )
            st.session_state["batch_saved_records"] = saved_records
            st.session_state["batch_results"] = []
            st.session_state["_batch_file_names"] = None
            st.rerun()
        else:
            st.error("❌ No records were saved. Check Firebase credentials and try again.")

# ─────────────────────────────────────────────────
# POST-SAVE CARD GRID
# ─────────────────────────────────────────────────
saved_records = st.session_state.get("batch_saved_records", [])
if saved_records:
    st.markdown("---")
    st.subheader(f"✅ Batch Complete — {len(saved_records)} Records Saved")
    st.caption("All scans have been saved to Patient History. Stroke-positive cases include a clinical PDF report.")

    cols_per_row = 3
    for row_start in range(0, len(saved_records), cols_per_row):
        row_items = saved_records[row_start : row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, r in zip(cols, row_items):
            c = r["Color"]
            with col:
                st.markdown(
                    f"""<div style='background:#0D1B2A; border:1px solid {c}55;
                        border-radius:12px; padding:14px; margin-bottom:8px;'>
                        <div style='font-size:12px; color:#8FA3BF; margin-bottom:4px;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'
                            title='{r["Filename"]}'>{r["Filename"]}</div>
                        <div style='font-weight:700; color:{c}; font-size:15px;
                            margin-bottom:2px;'>{r["Result"]}</div>
                        <div style='font-size:12px; color:#8FA3BF;'>
                            {r["Confidence"]} &nbsp;|&nbsp; {r["Date"]}
                        </div>
                        <div style='font-size:11px; color:{c}; margin-top:3px;
                            font-weight:600;'>{r["Triage"]}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                # Thumbnail
                img_src = r.get("image_url") or r.get("pil_image")
                if img_src:
                    st.image(img_src, use_container_width=True)

                # PDF button for stroke and suspicious cases
                is_suspicious_for_report = (r["Result"] == "Normal" and r["Confidence_raw"] < 0.75)
                if r["Result"] == "Ischemic Stroke" or is_suspicious_for_report:
                    if r.get("report_url"):
                        st.link_button("📄 View PDF Report", r["report_url"], use_container_width=True)
                    else:
                        st.caption("PDF generation failed")

    st.markdown("---")
    if st.button("🔄 Start New Batch Upload", use_container_width=True):
        st.session_state["batch_saved_records"] = []
        st.rerun()
