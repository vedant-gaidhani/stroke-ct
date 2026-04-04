import io
import os
import tempfile
from fpdf import FPDF
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
from .image_utils import format_confidence


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
    mask_present: bool = True,
    lesion_burden: int = None,
    extent_label: str = None,
    slices_with_lesion: int = None,
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
    fig_path  = _fig_to_temp_png(segmentation_fig) if segmentation_fig is not None else None

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
    pdf.set_xy(15, 7) # Explicit set to avoid margin overlap
    pdf.cell(0, 10, "NeuroTriage AI - Ischemic Stroke Detection Report", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.set_xy(15, 18) # Moved down to avoid overlap with title
    pdf.cell(0, 6, f"Generated: {scan_date}    |    Attending: Dr. {doctor_name}    |    {doctor_email}")
    pdf.set_y(28) # Move cursor to the end of the header block

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
    # Increase box height if we have lesion burden info
    box_height = 32 if (mask_present and lesion_burden is not None) else 22
    pdf.set_fill_color(*result_rgb)
    pdf.rect(15, box_y, 180, box_height, style="F")

    pdf.set_xy(15, box_y + 3)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.cell(90, 8, f"  {label.upper()}", align="L")
    pdf.cell(90, 8, f"Confidence: {format_confidence(confidence)}", align="R")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(180, 7, f"  Triage: {triage_text}", align="L")
    pdf.ln(9) # Reduced from 10 to keep inside box

    # Lesion Burden Info (if applicable)
    if mask_present and lesion_burden is not None:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*WHITE)
        burden_text = f"  Lesion Burden: {lesion_burden} pixels  |  Estimated Extent: {extent_label}  |  Involved Slices: {slices_with_lesion}"
        pdf.cell(180, 7, burden_text, align="L")
        pdf.ln(8)
    else:
        pdf.ln(4)

    # Recommendation
    if label == "Ischemic Stroke" and confidence >= 0.75:
        recommendation = "URGENT: Patient requires immediate neurological evaluation. Ischemic stroke suspected - consult stroke team."
    elif label == "Ischemic Stroke":
        recommendation = "NEEDS REVIEW: Moderate confidence for ischemic stroke. Radiologist review recommended before any clinical decision."
    else:
        recommendation = "No acute ischemic findings detected on this scan. Routine follow-up recommended if clinically indicated."

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(180, 5, f"Recommendation: {_sanitize(recommendation)}")
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

    # Original CT
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 5, "Original CT Scan (Uploaded Image)", ln=True)
    img_y = pdf.get_y()
    pdf.image(orig_path, x=15, y=img_y, w=85)
    pdf.ln(90)

    # AI Analysis panels (only for abnormal/suspicious cases)
    if fig_path is not None:
        lesion_note = "(lesion region detected)" if mask_present else "(no confident lesion region detected)"
        pdf.cell(0, 5, f"AI Analysis: Lesion Overlay | Model Attention Map | Combined View {lesion_note}", ln=True)
        pdf.image(fig_path, x=15, w=180)
        pdf.ln(6)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*GREY)
        pdf.multi_cell(180, 5, "No ischemic lesion localisation required. Stroke lesion overlay and model attention map are not generated for normal high-confidence results.")
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
        ("Classification",  "EfficientNet-B0  |  Validated Accuracy: 98.5%"),
        ("Segmentation",    "U-Net (Tversky Loss)  |  Dice: 0.5317  |  IoU: 0.4038"),
        ("Attention Map",   "Class Activation Map (CAM) - explanation aid, not segmentation boundary"),
        ("Seg. Config",     "threshold=0.45, keep_largest=True, weights fused 0.5/0.5"),
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
    if orig_path is not None and os.path.exists(orig_path):
        os.unlink(orig_path)
    if fig_path is not None and os.path.exists(fig_path):
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
