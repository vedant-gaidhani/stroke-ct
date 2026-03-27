import io
import os
import tempfile
from fpdf import FPDF
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib


# --- HELPERS ---
def _sanitize(text: str) -> str:
    """Replace non-Latin-1 characters to avoid FPDF font errors."""
    if not text: return ""
    # Map common problematic characters to ASCII
    mapping = {
        "\u2014": "-", # em-dash
        "\u2013": "-", # en-dash
        "\u2018": "'", # smart quote
        "\u2019": "'", # smart quote
        "\u201c": '"', # smart quote
        "\u201d": '"', # smart quote
    }
    for char, replacement in mapping.items():
        text = text.replace(char, replacement)
    # Encode to latin-1, ignoring errors, then decode back
    return text.encode("latin-1", "ignore").decode("latin-1")

def _hex_to_rgb(hex_color: str):
    """Convert #RRGGBB hex string to (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _pil_to_temp_png(pil_image) -> str:
    """Save a PIL image to a temporary PNG file and return the path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    pil_image.save(tmp.name, format="PNG")
    tmp.close()
    return tmp.name


def _fig_to_temp_png(fig) -> str:
    """Save a Matplotlib figure to a temporary PNG file and return the path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp.name, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    tmp.close()
    return tmp.name


# --- MAIN REPORT GENERATOR ---
def generate_clinical_report(
    patient_name: str,
    patient_id: str,
    scan_date: str,
    notes: str,
    label: str,
    confidence: float,
    triage_text: str,
    triage_color: str,
    original_image_pil,
    segmentation_fig,
    doctor_name: str,
    doctor_email: str,
) -> bytes:
    """
    Generates a clinical PDF report using fpdf2.
    Returns the PDF content as a bytes object.
    """
    # Color constants
    TEAL  = (29, 158, 117)
    WHITE = (255, 255, 255)
    DARK  = (10, 15, 30)
    GREY  = (170, 187, 212)
    RED   = (226, 75, 74)
    result_rgb = _hex_to_rgb(triage_color)

    # Sanitize inputs
    patient_name = _sanitize(patient_name)
    patient_id   = _sanitize(patient_id)
    notes        = _sanitize(notes)
    triage_text  = _sanitize(triage_text)
    doctor_name  = _sanitize(doctor_name)
    doctor_email = _sanitize(doctor_email)

    # Save images to temp files
    orig_path = _pil_to_temp_png(original_image_pil)
    fig_path  = _fig_to_temp_png(segmentation_fig)

    # ---- PDF Setup ----
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # ---- HEADER ----
    pdf.set_fill_color(*DARK)
    pdf.rect(0, 0, 210, 28, style="F")

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*TEAL)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "NeuroTriage AI - Clinical Stroke Detection Report", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.set_xy(15, 19)
    pdf.cell(0, 6, f"Generated: {scan_date}    |    Attending: Dr. {doctor_name}    |    {doctor_email}")
    pdf.ln(16)

    # Horizontal separator
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # ---- PATIENT INFO TABLE ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Patient Information", ln=True)
    pdf.ln(2)

    info_rows = [
        ("Patient Name", patient_name),
        ("Patient ID",   patient_id),
        ("Scan Date",    scan_date),
        ("Attending Physician", f"Dr. {doctor_name}"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for key, val in info_rows:
        pdf.set_fill_color(17, 34, 64)   # dark card color
        pdf.set_text_color(170, 187, 212)
        pdf.cell(60, 8, f"  {key}", border=0, fill=True)
        pdf.set_text_color(10, 15, 30)   # dark text to contrast white page
        pdf.cell(120, 8, f"  {val}", border=0, fill=False, ln=True)
    pdf.ln(5)

    # ---- AI RESULT BOX ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "AI Analysis Result", ln=True)
    pdf.ln(2)

    box_y = pdf.get_y()
    pdf.set_fill_color(*result_rgb)
    pdf.rect(15, box_y, 180, 22, style="F")

    pdf.set_xy(15, box_y + 3)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.cell(90, 8, f"  {label.upper()}", align="L")
    pdf.cell(90, 8, f"Confidence: {confidence*100:.1f}%", align="R")
    pdf.ln(10)

    pdf.set_xy(15, box_y + 13)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(180, 7, f"  Triage: {triage_text}", align="L")
    pdf.ln(14)

    # Recommendation text
    if label == "Stroke":
        recommendation = "URGENT: Patient requires immediate neurological evaluation and possible intervention."
    elif confidence < 0.75:
        recommendation = "LOW CONFIDENCE: Radiologist review is strongly recommended before any clinical decision."
    else:
        recommendation = "No acute hemorrhagic findings detected. Routine follow-up recommended."

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(180, 5, f"Recommendation: {recommendation}")
    pdf.ln(4)

    # ---- CT SCAN IMAGES ----
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "CT Scan Analysis Images", ln=True)
    pdf.ln(2)

    # Original CT (half page width on left)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 5, "Original CT Scan (Uploaded Image)", ln=True)
    img_y = pdf.get_y()
    pdf.image(orig_path, x=15, y=img_y, w=85)
    pdf.ln(90)

    # 4-Panel figure (full width)
    pdf.cell(0, 5, "AI Analysis: Segmentation Mask | Grad-CAM Heatmap | Combined Overlay", ln=True)
    pdf.image(fig_path, x=15, w=180)
    pdf.ln(6)

    # ---- CLINICAL NOTES ----
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Clinical Notes", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(10, 15, 30)   # dark text
    notes_text = notes if notes and notes.strip() else "No clinical notes provided."
    pdf.multi_cell(180, 6, notes_text)
    pdf.ln(4)

    # ---- MODEL INFORMATION ----
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Model Information", ln=True)
    pdf.ln(2)

    model_rows = [
        ("Classification Model", "EfficientNet-B0  |  Val Accuracy: 93.6%"),
        ("Segmentation Model",   "U-Net (Tversky Loss)  |  Dice Score: 0.89"),
        ("Explainability",       "Grad-CAM visualization (gradient-weighted class activation mapping)"),
    ]
    pdf.set_font("Helvetica", "", 9)
    for key, val in model_rows:
        pdf.set_text_color(170, 187, 212)
        pdf.cell(45, 7, f"  {key}:")
        pdf.set_text_color(10, 15, 30)   # dark text
        pdf.cell(135, 7, f" {val}", ln=True)
    pdf.ln(4)

    # ---- DISCLAIMER FOOTER ----
    if pdf.get_y() > 240:
        pdf.add_page()

    pdf.set_line_width(0.8)
    pdf.set_draw_color(*RED)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RED)
    pdf.cell(0, 5, "WARNING: DISCLAIMER", ln=True)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, "DISCLAIMER: This report is generated by an AI model and should be reviewed by a qualified radiologist before making any clinical "
                         "decision. Not for standalone diagnostic use. NeuroTriage AI is a decision-support tool only.")

    # Page number
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 10, f"Page {pdf.page_no()}", align="R")

    # ---- CLEANUP TEMP FILES ----
    os.unlink(orig_path)
    os.unlink(fig_path)

    # Return as bytes
    return bytes(pdf.output())


# --- HELPER: SAVE BYTES TO FILE ---
def save_pdf_bytes_to_file(pdf_bytes: bytes, filename: str) -> str:
    """
    Saves PDF bytes to a temporary file.
    Returns the path to the saved file.
    """
    tmp_dir = tempfile.gettempdir()
    file_path = os.path.join(tmp_dir, filename)
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
    return file_path
