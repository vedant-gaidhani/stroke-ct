# NeuroTriage AI 🧠

> **AI-powered Brain Stroke Detection and Lesion Segmentation from CT Scans**

A clinical-grade web application built for the *AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans* hackathon. NeuroTriage AI combines a state-of-the-art dual-model inference pipeline with a premium, dark-themed clinical dashboard — designed to assist radiologists and emergency physicians in rapid stroke triage.

---

## ✨ Key Features

- **Stroke Classification** — EfficientNet-B0 classifier (98.5% accuracy) detects Ischemic Stroke vs. Normal in seconds.
- **Lesion Segmentation** — Dual U-Net pipeline (Tversky Loss, Dice optimised) generates pixel-level lesion overlays.
- **Model Attention Map** — Per-case Grad-CAM explanation overlay, anatomically locked to brain parenchyma. Clearly labeled as an *explanation aid*, not a diagnostic boundary.
- **Multi-Slice Analysis** — Processes full DICOM/multi-slice studies with per-slice results and lesion burden estimates.
- **Batch Upload** — Analyse multiple CT scans simultaneously with a summary results table and individual PDF reports.
- **Clinical PDF Reports** — Auto-generated reports with patient info, AI result, segmentation images, and a mandatory clinical disclaimer.
- **Patient History & Alerts** — Firebase-backed patient records, doctor alert system, and email notifications via SendGrid.
- **Role-based Auth** — Secure Firebase Authentication with Doctor and Nurse roles.

---

## 🗂️ Repository Structure

```
app/                    # Streamlit multi-page clinical application
├── app.py              # Entry point and auth gate
├── landing_ui.py       # Premium landing page with 3D brain model
├── mock_models.py      # Demo inference + attention map generation
├── real_models.py      # Live EfficientNet + U-Net inference pipeline
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_New_Scan.py
│   ├── 3_Patient_History.py
│   ├── 4_Batch_Upload.py
│   └── 5_Reports.py
├── app_utils/
│   ├── pdf_generator.py
│   ├── image_utils.py
│   ├── cloudinary_utils.py
│   └── email_utils.py
└── assets/
    ├── style.css
    ├── attention_maps/     # Place precomputed .png attention maps here
    └── images/

classification/         # EfficientNet-B0 training and evaluation
segmentation/           # U-Net training and evaluation
src/                    # Shared pipeline contracts and utilities
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/neurotriage-ai.git
cd neurotriage-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create `app/.env` from the template:
```bash
cp app/.env.example app/.env
```
Fill in your Firebase, Cloudinary, and SendGrid credentials.

### 4. Add Firebase credentials
Place your Firebase service account key at `app/serviceAccountKey.json`.  
> ⚠️ **Never commit this file.** It is already in `.gitignore`.

### 5. Add model checkpoints *(optional, for live inference)*
```powershell
$env:STROKE_CT_CLASSIFICATION_CHECKPOINT="path\to\classifier_best_efficientnet_b0.pth"
$env:STROKE_CT_SEGMENTATION_CHECKPOINT="path\to\segmentor_best_tversky_384.pth"
```
Without checkpoints, the app automatically falls back to the mock inference pipeline for demo purposes.

### 6. Run the app
```bash
cd app
streamlit run app.py
```

---

## 🧪 Model Information

| Component | Architecture | Metric |
|---|---|---|
| Classification | EfficientNet-B0 | Accuracy: 98.5% |
| Segmentation | U-Net (Tversky Loss) | Dice: 0.5317 · IoU: 0.4038 |
| Attention Map | Grad-CAM (Explanation Aid) | Anatomically masked |

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `FIREBASE_CREDENTIALS_PATH` | Path to `serviceAccountKey.json` |
| `FIREBASE_STORAGE_BUCKET` | Firebase Storage bucket name |
| `FIREBASE_WEB_API_KEY` | Firebase Web API Key |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `SENDGRID_API_KEY` | SendGrid API key for email alerts |

---

## ⚠️ Clinical Disclaimer

> This application is an **AI-assisted decision support tool** only. All results, including stroke classification, lesion overlays, and attention maps, must be reviewed by a qualified radiologist or physician before any clinical action is taken. **Not for standalone diagnostic use.**

---

## 📄 License

This repository is for educational and hackathon demonstration purposes.
