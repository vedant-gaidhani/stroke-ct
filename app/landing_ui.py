import base64
import os
import streamlit as st

def load_img_b64(filename):
    path = os.path.join(os.path.dirname(__file__), "assets", "images", filename)
    with open(path, "rb") as f:
        data = f.read()
    ext = filename.split('.')[-1]
    return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"

try:
    IMG_WHISK = load_img_b64("Whisk_b14d1c2fee4fe1c9ddd492ce0dddfefcdr.png")
    IMG_SEGMENTATION = load_img_b64("feature-segmentation-.webp")
    IMG_TRIAGE = load_img_b64("feature-triage.webp")
except Exception as e:
    IMG_WHISK = ""
    IMG_SEGMENTATION = ""
    IMG_TRIAGE = ""

def get_features_html():
    """Returns a fully self-contained HTML doc for the Bento Grid + Modal.
    Must use components.html() so JS onclick handlers actually execute."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ background: transparent; font-family: 'Space Grotesk', sans-serif; color: #fff; }}
  body {{ padding: 0 1rem 2rem 1rem; }}

  .section-title {{ font-size: 36px; font-weight: 800; margin-bottom: 1.5rem; letter-spacing: -2px; color: #fff; }}

  .bento-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: auto auto;
    gap: 1rem;
  }}
  @media (max-width: 768px) {{
    body {{ padding: 0 0.5rem 2rem 0.5rem; }}
    .section-title {{ font-size: 22px !important; letter-spacing: -0.5px; }}
    .bento-grid {{ grid-template-columns: 1fr !important; }}
    .card-large {{ grid-column: span 1 !important; grid-row: span 1 !important; }}
    .card-large .bento-visual {{ min-height: 160px !important; }}
    .bento-title {{ font-size: 16px !important; }}
    .bento-desc {{ font-size: 12px !important; }}
    .card-large .bento-title {{ font-size: 22px !important; }}
    .card-large .bento-desc {{ font-size: 13px !important; }}
    .fm-box {{ max-width: 95vw !important; }}
    .fm-header {{ padding: 1.25rem 1.25rem 1rem !important; }}
    .fm-title {{ font-size: 20px !important; }}
    .fm-media {{ margin: 0 1.25rem !important; height: 120px !important; }}
    .fm-body {{ padding: 1.25rem !important; }}
    .fm-footer {{ padding: 1rem 1.25rem 1.25rem !important; }}
  }}
  .bento-card {{
    background: #09090b;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.8rem;
    display: flex;
    flex-direction: column;
    min-height: 180px;
    transition: all 0.3s cubic-bezier(0.175,0.885,0.32,1.275);
    overflow: hidden;
    position: relative;
    cursor: pointer;
  }}
  .bento-card:hover {{ border-color: #00f2fe; transform: translateY(-4px) scale(1.01); box-shadow: 0 15px 40px rgba(0,242,254,0.08); }}
  .card-large {{ grid-column: span 2; grid-row: span 2; padding: 2rem; min-height: unset; }}
  .bento-icon {{ font-size: 22px; margin-bottom: 0.75rem; display: inline-flex; color: #00f2fe; }}
  .bento-title {{ font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 6px; letter-spacing: -0.5px; }}
  .bento-desc {{ font-size: 13px; color: #8892A4; line-height: 1.4; }}
  .card-large .bento-title {{ font-size: 28px; letter-spacing: -1px; margin-bottom: 8px; }}
  .card-large .bento-desc {{ font-size: 15px; }}
  .bento-visual {{
    flex-grow: 1; margin-top: 1.5rem; border-radius: 12px;
    background: #000; position: relative;
    border: 1px solid rgba(255,255,255,0.04);
    min-height: 110px; overflow: hidden;
  }}
  .card-large .bento-visual {{ min-height: 260px; margin-top: 2rem; }}

  /* --- MODAL --- */
  .fm-overlay {{
    display: none; position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(0,0,0,0.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 9999;
    align-items: center; justify-content: center; padding: 1rem;
  }}
  .fm-overlay.open {{ display: flex; }}
  .fm-box {{
    background: #09090b; width: 100%; max-width: 600px;
    max-height: 90vh; overflow-y: auto;
    border-radius: 16px;
    border: 1px solid rgba(0,242,254,0.3);
    box-shadow: 0 10px 40px rgba(0,242,254,0.15);
    display: flex; flex-direction: column;
    animation: slideDown 0.3s ease-out;
  }}
  @keyframes slideDown {{ from {{ opacity:0; transform:translateY(-20px); }} to {{ opacity:1; transform:translateY(0); }} }}
  .fm-header {{ padding: 2rem 2rem 1.5rem; display: flex; justify-content: space-between; align-items: flex-start; }}
  .fm-title {{ color: #fff; font-size: 26px; font-weight: 800; letter-spacing:-1px; margin-bottom:6px; }}
  .fm-sub {{ color: #8892A4; font-size: 14px; }}
  .fm-close {{
    background: transparent; border: 1px solid rgba(0,242,254,0.3);
    color: #00f2fe; width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 16px; flex-shrink: 0;
    transition: all 0.2s;
  }}
  .fm-close:hover {{ background: rgba(0,242,254,0.1); transform: scale(1.1); }}
  .fm-media {{
    margin: 0 2rem; height: 180px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px; display: flex;
    flex-direction: column; align-items: center; justify-content: center;
  }}
  .fm-body {{ padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }}
  .fm-section-title {{ color: #fff; font-weight: 700; font-size: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
  .fm-desc {{ color: #8892A4; font-size: 14px; line-height: 1.6; }}
  .fm-bens {{ color: #8892A4; font-size: 14px; line-height: 1.8; padding-left: 1.2rem; }}
  .fm-spec {{
    padding: 10px 14px; border: 1px solid rgba(0,242,254,0.2);
    border-radius: 8px; background: rgba(0,242,254,0.02);
    font-size: 13px; color: #a3e0f0; font-family: monospace;
    margin-bottom: 8px;
  }}
  .fm-footer {{
    padding: 1rem 2rem 1.5rem; border-top: 1px solid rgba(255,255,255,0.05);
    display: flex; gap: 12px;
  }}
  .fm-btn-close {{
    flex: 1; padding: 12px; background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
    color: #fff; border-radius: 8px; font-weight: 600;
    cursor: pointer; transition: all 0.2s; font-family: 'Space Grotesk', sans-serif; font-size: 14px;
  }}
  .fm-btn-close:hover {{ background: rgba(255,255,255,0.05); transform: translateY(-2px); }}
  .fm-btn-learn {{
    flex: 1; padding: 12px; background: #00f2fe; border: none;
    color: #000; border-radius: 8px; font-weight: 700;
    cursor: pointer; transition: all 0.2s; font-family: 'Space Grotesk', sans-serif; font-size: 14px;
  }}
  .fm-btn-learn:hover {{ background: #7ffeff; transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,242,254,0.4); }}
</style>
</head>
<body>
  <h2 class="section-title">Comprehensive Platform</h2>
  <div class="bento-grid">

    <!-- 1. Large card -->
    <div class="bento-card card-large"
      onclick="openFModal(this)"
      data-title="AI Stroke Detection"
      data-sub="Deep learning classification with 93.1% accuracy"
      data-desc="Our proprietary deep learning model achieves 93.1% accuracy in stroke detection with 97.9% AUC. Built on EfficientNet-B0 architecture and trained on thousands of clinical CT scans, it identifies ischemic strokes in real-time with exceptional precision."
      data-bens="Real-time stroke detection in under 2 seconds|93.1% accuracy with 97.9% AUC score|Reduces false positives by 40% compared to traditional methods|Integrates seamlessly with existing hospital PACS systems"
      data-specs="Model: EfficientNet-B0 with custom lesion-aware classification|Input: DICOM or standard image formats (JPG, PNG)|Output: Confidence score + clinical risk category|Processing time: < 2 seconds per scan">
      <div><div class="bento-title">AI Stroke Detection</div><p class="bento-desc">Deep learning classification with 93.1% accuracy</p></div>
      <div class="bento-visual" style="background:#000;">
        <div style="position:absolute;width:100%;height:100%;top:0;left:0;background:radial-gradient(circle at center,rgba(0,242,254,0.1),transparent 70%);"></div>
        <img src="{IMG_WHISK}" style="width:100%;height:100%;object-fit:cover;position:relative;z-index:2;border-radius:12px;opacity:0.85;mix-blend-mode:screen;" />
      </div>
    </div>

    <!-- 2. Clinical Explainability -->
    <div class="bento-card"
      onclick="openFModal(this)"
      data-title="Clinical Explainability"
      data-sub="Grad-CAM heatmaps show AI reasoning"
      data-desc="Explore critical findings through our interactive 3D viewer. We leverage Grad-CAM to overlay high-fidelity spatial heatmaps directly onto the DICOM slices, ensuring complete clinical transparency."
      data-bens="Real-time 3D rendering|Multi-planar reconstruction (MPR)|Measure lesion volumes dynamically|Toggle tissue density thresholds"
      data-specs="Render Engine: WebGL/Three.js|Latency: < 50ms interaction loop|Volumetric accuracy: 0.1 cubic mm">
      <div class="bento-icon">⚡</div>
      <div class="bento-title">Clinical Explainability</div>
      <p class="bento-desc">Grad-CAM heatmaps show AI reasoning</p>
    </div>

    <!-- 3. Batch Processing -->
    <div class="bento-card"
      onclick="openFModal(this)"
      data-title="Batch Processing"
      data-sub="Process multiple scans simultaneously"
      data-desc="Built for high-volume diagnostic centers. Upload massive ZIP folders of CT series and our dynamic scheduling engine automatically allocates GPU resources to process them in parallel."
      data-bens="Unlimited queue scaling|Asynchronous background tasks|Automatic PDF generation|Status webhooks integration"
      data-specs="Queue System: Native async pool|Max concurrent nodes: 124|Failover handling: Auto-retry on CUDA OOM">
      <div class="bento-icon">📊</div>
      <div class="bento-title">Batch Processing</div>
      <p class="bento-desc">Process multiple scans simultaneously</p>
    </div>

    <!-- 4. Lesion Segmentation -->
    <div class="bento-card"
      onclick="openFModal(this)"
      data-title="Lesion Segmentation"
      data-sub="U-Net powered ischemic lesion localisation"
      data-desc="Pinpoint exact stroke regions using our advanced image segmentation overlays. Highlights specific borders of ischemic core and penumbra, enabling rapid clinical assessment of tissue at risk."
      data-bens="Pixel-perfect boundary generation|Contrast-independent mask creation|Supports diverse slice thickness levels"
      data-specs="Algorithm: 3D U-Net variant|Mask resolution: Native equivalent|IoU Score: 0.81 clinical benchmark">
      <div class="bento-title">Lesion Segmentation</div>
      <p class="bento-desc">U-Net powered ischemic lesion localisation</p>
      <div class="bento-visual" style="display:flex;align-items:center;justify-content:center;">
        <img src="{IMG_SEGMENTATION}" style="width:100%;height:100%;object-fit:contain;border-radius:8px;opacity:0.9;mix-blend-mode:screen;" />
      </div>
    </div>

    <!-- 5. Confidence-Based Triage -->
    <div class="bento-card"
      onclick="openFModal(this)"
      data-title="Confidence-Based Triage"
      data-sub="Automatic risk stratification"
      data-desc="Our AI immediately assigns a confidence score to every processed scan. High-risk results instantly float to the top of your queue and can trigger webhooks to clinical pager systems."
      data-bens="Zero-delay SMS/Pager routing|Color-coded priority queueing|Customizable threshold triggers"
      data-specs="Risk logic: Multi-variate bayesian|Latency: Instant post-inference|Alert channels: SMS, Webhook, HL7">
      <div class="bento-title">Confidence-Based Triage</div>
      <p class="bento-desc">Automatic risk stratification</p>
      <div class="bento-visual" style="display:flex;align-items:center;justify-content:center;">
        <img src="{IMG_TRIAGE}" style="width:90%;height:90%;object-fit:contain;border-radius:8px;opacity:0.9;mix-blend-mode:screen;" />
      </div>
    </div>

    <!-- 6. Automated Reporting -->
    <div class="bento-card"
      onclick="openFModal(this)"
      data-title="Automated Reporting"
      data-sub="Generate PDF reports at scale"
      data-desc="Replace manual transcriptions with one-click, HIPAA-compliant clinical reports. Our engine automatically structures metadata, DICOM header info, and AI prediction heatmaps into a clean PDF format."
      data-bens="Standardized clinical formatting|Embedded DICOM preview slices|Includes complete metadata extraction"
      data-specs="Generation Engine: Custom templating|Formats: PDF, JSON, HL7|Export support: Direct to EHR">
      <div class="bento-icon">🕒</div>
      <div class="bento-title">Automated Reporting</div>
      <p class="bento-desc">Generate PDF reports at scale</p>
    </div>

  </div><!-- end .bento-grid -->

  <!-- MODAL -->
  <div id="featModal" class="fm-overlay" onclick="handleOverlayClick(event)">
    <div class="fm-box">
      <div class="fm-header">
        <div>
          <div id="fmTitle" class="fm-title">Title</div>
          <div id="fmSub" class="fm-sub">Subtitle</div>
        </div>
        <button class="fm-close" onclick="closeFModal()">✕</button>
      </div>
      <div class="fm-media">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:8px;">
          <circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon>
        </svg>
        <span style="color:#8892A4;font-size:12px;">Click to play demo</span>
      </div>
      <div class="fm-body">
        <div>
          <div class="fm-section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Overview
          </div>
          <p id="fmDesc" class="fm-desc"></p>
        </div>
        <div>
          <div class="fm-section-title">Key Benefits</div>
          <ul id="fmBens" class="fm-bens"></ul>
        </div>
        <div>
          <div class="fm-section-title">Technical Specifications</div>
          <div id="fmSpecs"></div>
        </div>
      </div>
      <div class="fm-footer">
        <button class="fm-btn-close" onclick="closeFModal()">Close</button>
        <button class="fm-btn-learn">Learn More</button>
      </div>
    </div>
  </div>

  <script>
    function openFModal(el) {{
      document.getElementById('fmTitle').innerText = el.dataset.title || '';
      document.getElementById('fmSub').innerText = el.dataset.sub || '';
      document.getElementById('fmDesc').innerText = el.dataset.desc || '';
      var bens = (el.dataset.bens || '').split('|').filter(Boolean);
      document.getElementById('fmBens').innerHTML = bens.map(function(b){{ return '<li>' + b + '</li>'; }}).join('');
      var specs = (el.dataset.specs || '').split('|').filter(Boolean);
      document.getElementById('fmSpecs').innerHTML = specs.map(function(s){{ return '<div class="fm-spec">' + s + '</div>'; }}).join('');
      document.getElementById('featModal').classList.add('open');
    }}
    function closeFModal() {{
      document.getElementById('featModal').classList.remove('open');
    }}
    function handleOverlayClick(e) {{
      if (e.target === document.getElementById('featModal')) closeFModal();
    }}
    // Auto-resize: tell Streamlit the exact height of this iframe content
    function sendHeight() {{
      var h = document.body.scrollHeight;
      window.parent.postMessage({{type: 'streamlit:setFrameHeight', height: h}}, '*');
    }}
    window.addEventListener('load', sendHeight);
    new ResizeObserver(sendHeight).observe(document.body);
  </script>
</body>
</html>"""

LANDING_CSS = """
<style>
/* Reset and Font */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap');
* { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.05em; }
.stat-val, .metric-val { font-family: 'Space Mono', monospace; letter-spacing: normal; }

/* Hide Streamlit Chrome entirely */
#MainMenu { display: none !important; }
header[data-testid="stHeader"], [data-testid="stHeader"], header { display: none !important; }
footer { display: none !important; }
[data-testid="stSidebar"] {display: none !important;}
.stApp {background-color: #050505; color: white; background-image: none;}

/* Break out of Streamlit container ONLY for full-width components via VW */
.block-container {
    max-width: 1600px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Header */
.btn-hover-glow { transition: all 0.2s; }
.btn-hover-glow:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 242, 254, 0.2); }

.landing-header {
    position: fixed; top: 0; left: 0; z-index: 1000;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    height: 72px;
    width: 100vw;
    margin: 0;
    animation: slideDown 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.header-inner {
    max-width: 1600px; margin: 0 auto; padding: 0 2rem;
    display: grid; 
    grid-template-columns: 1fr auto 1fr; 
    align-items: center; 
    height: 100%;
}
.landing-logo { display: flex; align-items: center; gap: 12px; justify-self: start; }
.logo-dot { width: 8px; height: 8px; background: #00f2fe; border-radius: 50%; box-shadow: 0 0 4px #00f2fe; animation: pulse-cyan 2s infinite; }
@keyframes pulse-cyan { 0%,100% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 6px #00f2fe; } }
.logo-text { font-size: 20px; font-weight: 700; color: #fff; letter-spacing: -0.3px; display: flex; align-items: center; gap: 12px;}
.landing-nav { display: flex; align-items: center; gap: 4px; justify-self: center; background: rgba(255,255,255,0.03); padding: 4px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
.nav-item { padding: 8px 16px; border-radius: 8px; font-size: 13px; color: rgba(255,255,255,0.6); cursor: pointer; transition: all .3s cubic-bezier(0.4, 0, 0.2, 1); font-weight: 500; }
.nav-item:hover { background: rgba(0, 242, 254, 0.1); color: #fff; transform: translateY(-1px); }
.nav-item.active { background: rgba(0, 242, 254, 0.2); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.2); }

/* Hero Top Elements */
.hero-wrapper {
    padding: 6rem 8rem 1rem 12rem; /* Increased left padding to shift right */
    max-width: 1600px;
    margin: 0 auto;
}
.hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.2); padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #00f2fe; margin-bottom: 2rem; text-transform: uppercase; letter-spacing: 1px; animation: fadeInUpGlob 0.8s ease-out backwards; }
.hero-badge-dot { width: 6px; height: 6px; background: #00f2fe; border-radius: 50%; animation: breathe 2s ease-in-out infinite; box-shadow: 0 0 8px #00f2fe; }
.hero-title { font-size: 64px; font-weight: 900; line-height: 1.0; margin-bottom: 1.5rem; letter-spacing: -3px; margin-top: 0; color: white; animation: typeReveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.3s backwards;}
.hero-title span { background: linear-gradient(135deg, #00f2fe 0%, #00b4fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: none; }
.hero-sub { font-size: 18px; color: #a3a3a3; line-height: 1.6; margin-bottom: 2.5rem; max-width: 540px; animation: fadeInUpGlob 1s ease-out 0.6s backwards; font-weight: 400; }

/* Streamlit Native Form overrides inside the Hero */
div[data-testid="stTabs"] {
    max-width: 480px;
    background: rgba(255, 255, 255, 0.02);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    backdrop-filter: blur(10px);
}
.stTabs [data-baseweb="tab-list"] { background-color: rgba(255, 255, 255, 0.03); padding: 4px; border-radius: 8px; border-bottom: none; gap: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 6px; color: #8892A4; padding: 6px 12px; border-bottom: none !important; }
.stTabs [aria-selected="true"] { background-color: rgba(0, 242, 254, 0.2) !important; color: #00f2fe !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTextInput input { background-color: rgba(0, 0, 0, 0.4) !important; backdrop-filter: blur(8px); color: white !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 8px !important; }
.stTextInput input:focus { border-color: rgba(255, 255, 255, 0.15) !important; box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) !important; }
.stButton button { width: 100%; background: rgba(255, 255, 255, 0.10) !important; color: white !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 8px !important; font-weight: 600 !important; padding: 0.5rem 1rem !important; transition: all 0.3s; margin-top: 10px; }
.stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 242, 254, 0.1) !important; }

/* Grid stats underneath form */
.hero-stats { display: flex; gap: 2.5rem; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1); max-width: 480px; }
.stat { text-align: center; }
.stat-val { font-size: 24px; font-weight: 800; color: #00f2fe; }
.stat-label { font-size: 12px; color: #8892A4; margin-top: 2px; }

/* Full bleed sections */
.features-section { background: rgba(255, 255, 255, 0.01); backdrop-filter: blur(10px); padding: 5rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); margin-top: 1rem; width: 100vw; position: relative; left: 50%; margin-left: -50vw; }
.metrics-section { background: rgba(255, 255, 255, 0.01); backdrop-filter: blur(10px); padding: 5rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); width: 100vw; position: relative; left: 50%; margin-left: -50vw; }
.section-inner { max-width: 1600px; margin: 0 auto; padding: 0 1rem; }


.section-tag { font-size: 12px; color: #00f2fe; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 0.5rem; display: inline-block; background: rgba(0, 242, 254, 0.15); padding: 4px 10px; border-radius: 4px; position: relative; overflow: hidden; }
.section-tag::after { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent); animation: shimmerSweep 3s infinite; }

.section-title { font-size: 32px; font-weight: 700; margin-bottom: 0.5rem; color: white; margin-top: 0; animation: fadeInUpGlob 0.8s ease-out 0.15s backwards;}
.section-sub { font-size: 15px; color: #8892A4; margin-bottom: 3.5rem; animation: fadeInUpGlob 0.8s ease-out 0.3s backwards; }


/* -------------------------------- */
/* AWARD-WINNING ANIMATIONS LIBRARY */
/* -------------------------------- */
@keyframes fadeInUpGlob {
    from { opacity: 0; transform: translateY(40px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes floatGlob {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
}

@keyframes shimmerSweep {
    0% { left: -100%; }
    50% { left: 200%; }
    100% { left: 200%; }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 8px rgba(0, 242, 254, 0.3); }
    50% { box-shadow: 0 0 20px rgba(0, 242, 254, 0.8), 0 0 40px rgba(0, 242, 254, 0.2); }
}

@keyframes spin-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes pulse-ring {
    0%, 100% { opacity: 1; border-color: rgba(0, 242, 254, 0.4); }
    50% { opacity: 0.4; border-color: rgba(0, 242, 254, 0.1); }
}
/* -------------------------------- */

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-100%); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes typeReveal {
    from { opacity: 0; clip-path: inset(0 100% 0 0); }
    to { opacity: 1; clip-path: inset(0 0% 0 0); }
}

@keyframes cardShimmer {
    0% { left: -100%; opacity: 0; }
    50% { opacity: 1; }
    100% { left: 200%; opacity: 0; }
}

@keyframes breathe {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.5); }
}

@keyframes countUp {
    from { opacity: 0; transform: translateY(20px) scale(0.9); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Bento Grid Layout */
.bento-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: minmax(130px, auto);
    gap: 1rem;
    margin-top: 1rem;
}

.bento-card {
    background: #09090b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.8rem;
    display: flex;
    flex-direction: column;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    overflow: hidden;
    position: relative;
    animation: fadeInUpGlob 0.8s ease-out backwards;
}

.bento-card:nth-child(1) { animation-delay: 0.1s; }
.bento-card:nth-child(2) { animation-delay: 0.2s; }
.bento-card:nth-child(3) { animation-delay: 0.3s; }
.bento-card:nth-child(4) { animation-delay: 0.4s; }
.bento-card:nth-child(5) { animation-delay: 0.5s; }
.bento-card:nth-child(6) { animation-delay: 0.6s; }

.bento-card:hover { border-color: #00f2fe; transform: translateY(-4px) scale(1.01); box-shadow: 0 15px 40px rgba(0, 242, 254, 0.05); z-index: 10; }

.card-large {
    grid-column: span 2;
    grid-row: span 2;
    padding: 2rem;
}

/* Base Bento Elements */
.bento-icon { font-size: 24px; margin-bottom: 1rem; display: inline-flex; color: #00f2fe;}
.bento-title { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 6px; margin-top: 0; letter-spacing: -0.5px; }
.bento-desc { font-size: 13px; color: #8892A4; margin-bottom: 0; line-height: 1.4; font-weight: 400;}

.card-large .bento-title { font-size: 28px; letter-spacing: -1px; margin-bottom: 8px;}
.card-large .bento-desc { font-size: 15px; }

/* Visual Placeholders for Cards */
.bento-visual {
    flex-grow: 1;
    margin-top: 1.5rem;
    border-radius: 12px;
    background: #000;
    position: relative;
    border: 1px solid rgba(255, 255, 255, 0.04);
    min-height: 110px;
    overflow: hidden;
}

.card-large .bento-visual { min-height: 260px; margin-top: 2rem; }

/* CSS Art for Brain Scan large card */
.brain-visual {
    background: #000 radial-gradient(circle at 60% 40%, rgba(196, 240, 21, 0.10) 0%, transparent 60%);
    display: flex; align-items: center; justify-content: center;
}
.brain-visual::after { content: '🧠'; font-size: 280px; opacity: 0.1; filter: grayscale(1); }
.lesion-glow {
    position: absolute; right: 22%; top: 35%; width: 15%; height: 25%;
    border-radius: 50% 60% 40% 60%;
    background: #c4f015; filter: blur(35px); opacity: 0.4;
    animation: pulsateGlow 3s ease-in-out infinite; box-shadow: 0 0 80px #c4f015;
}
.scan-overlay {
    position: absolute; width: 100%; height: 100%; top: 0; left: 0;
    background: linear-gradient(0deg, rgba(0,0,0,0) 48%, rgba(196,240,21,0.05) 50%, rgba(0,0,0,0) 52%);
    background-size: 100% 12px; z-index: 5; pointer-events: none; opacity: 0.3;
}

@keyframes pulsateGlow { 0%, 100% { transform: scale(1); opacity: 0.4; } 50% { transform: scale(1.1); opacity: 0.7; } }

/* Slice Visual Art */
.slice-visual { background: #000; perspective: 800px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 20px; }
.slice { border: 1px solid #c4f015; border-radius: 50%; width: 50%; height: 40px; position: absolute; background: rgba(196, 240, 21, 0.05); }
.s1 { transform: rotateX(70deg) translateZ(30px) scale(0.6); border-color: #00f2fe; background: rgba(0,242,254,0.1); }
.s2 { transform: rotateX(70deg) translateZ(0px) scale(0.8); border-color: #c4f015; box-shadow: 0 0 20px rgba(196,240,21,0.2); z-index: 2;}
.s3 { transform: rotateX(70deg) translateZ(-30px) scale(1); border-color: #ff0844; background: rgba(255,8,68,0.1); }

/* Pyramid Visual Art */
.pyramid-visual { background: #000; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 1rem; }
.pyramid { display: flex; flex-direction: column; align-items: center; width: 100%; position: relative; }
.pyramid::before { content: ''; position: absolute; width: 100%; height: 100px; background: rgba(255,8,68,0.15); filter: blur(40px); bottom: 0px; z-index: 0; pointer-events: none;}
.p-top { width: 0; border-left: 40px solid transparent; border-right: 40px solid transparent; border-bottom: 50px solid rgba(196,240,21,0.8); margin-bottom: 3px; z-index: 1;}
.p-mid { width: 0; border-left: 80px solid transparent; border-right: 80px solid transparent; border-bottom: 50px solid #ef9f27; margin-bottom: 3px; z-index: 1;}
.p-bot { width: 0; border-left: 120px solid transparent; border-right: 120px solid transparent; border-bottom: 50px solid rgba(255,8,68,0.9); z-index: 1;}

@media (max-width: 1024px) {
    .bento-grid { grid-template-columns: 1fr; }
    .card-large { grid-column: span 1; grid-row: span 1; padding: 2rem; }
    .card-large .bento-visual { min-height: 250px; }
}

.metrics-section { background: #050505; padding: 8rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); width: 100vw; position: relative; left: 50%; margin-left: -50vw; overflow: hidden;}
.metrics-flex-row { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; margin-top: 5rem; padding-bottom: 2rem; position: relative; z-index: 10; }

.metric-item { display: flex; flex-direction: column; align-items: flex-start; gap: 1.5rem; animation: floatGlob 6s ease-in-out infinite; }
.metric-item:nth-child(1) { animation-delay: 0s; }
.metric-item:nth-child(2) { animation-delay: -1s; }
.metric-item:nth-child(3) { animation-delay: -2.5s; }
.metric-item:nth-child(4) { animation-delay: -0.5s; }
.metric-item:nth-child(5) { animation-delay: -4s; }

.m-val { font-size: 72px; font-weight: 300; color: #ffffff; font-family: 'Space Mono', monospace; line-height: 1; letter-spacing: -0.05em; text-shadow: 0 4px 20px rgba(0,0,0,0.8); animation: countUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) backwards; }
.m-lbl { display: flex; align-items: center; gap: 10px; font-size: 11px; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 4px; font-weight: 700; }
.m-dot { width: 6px; height: 6px; border-radius: 50%; animation: breathe 3s ease-in-out infinite; }
.dot-cyan { background: #00f2fe; box-shadow: 0 0 8px rgba(0, 242, 254, 0.3); }
.dot-red { background: #ff0844; box-shadow: 0 0 8px rgba(255, 8, 68, 0.3); }


/* Activity Cards */
.activity-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 5rem; padding-top: 4rem; border-top: 1px solid rgba(255,255,255,0.05); position: relative; z-index: 10;}
.act-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); animation: fadeInUpGlob 0.6s ease-out backwards; }
.act-card:nth-child(1) { animation-delay: 0.1s; }
.act-card:nth-child(2) { animation-delay: 0.2s; }
.act-card:nth-child(3) { animation-delay: 0.3s; }
.act-card:nth-child(4) { animation-delay: 0.4s; }
.act-card:hover { border-color: rgba(255, 255, 255, 0.15); transform: translateY(-4px) scale(1.01); box-shadow: 0 15px 30px -10px rgba(0,0,0,0.8); }
.act-header { display: flex; align-items: center; margin-bottom: 8px; }
.act-dot { width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 4px currentColor; animation: breathe 2.5s ease-in-out infinite; }
.act-title { font-size: 13px; font-weight: 600; color: #fff; letter-spacing: 0.5px; }
.act-desc { font-size: 12px; color: #8892A4; line-height: 1.5; margin-bottom: 12px; flex-grow: 1; }
.act-time { font-size: 10px; color: rgba(255,255,255,0.3); font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: 1px; }

.status-cyan { background: #00f2fe; color: #00f2fe; }
.status-red { background: #ff0844; color: #ff0844; }
.status-purple { background: #be5cff; color: #be5cff; }
/* Footer */
.footer { padding: 4rem 1rem 8rem 1rem; width: 100vw; position: relative; left: 50%; margin-left: -50vw; display: flex; justify-content: center; background: transparent; overflow: hidden; align-items: center; }

.footer-watermark {
    position: absolute; bottom: -8%; left: 50%; transform: translateX(-50%);
    font-size: 260px; font-weight: 900; color: rgba(255, 255, 255, 0.02);
    z-index: 0; white-space: nowrap; pointer-events: none;
    font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.05em;
}

.footer-card {
    background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(24px); border-radius: 32px; padding: 4rem 4rem 2rem 4rem;
    width: 100%; max-width: 1200px; z-index: 10; position: relative;
    box-shadow: inset 0 2px 20px rgba(255,255,255,0.02), 0 30px 60px -15px rgba(0,0,0,0.8);
}

.footer-top {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding-bottom: 3rem; border-bottom: 1px solid rgba(255,255,255,0.05); gap: 2rem;
}

.footer-brand { max-width: 380px; }
.footer-brand-title { display: flex; align-items: center; gap: 12px; font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 1.5rem; letter-spacing: -0.3px; }
.footer-logo-icon { width: 28px; height: 28px; background: #00f2fe; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; transform: rotate(-10deg); color: #000; box-shadow: 0 0 15px rgba(0,242,254,0.4); }

.footer-brand-desc { font-size: 14px; color: #8892A4; line-height: 1.6; margin-bottom: 2rem; }

.footer-socials { display: flex; gap: 12px; }
.social-icon { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; color: #fff !important; transition: all 0.3s; cursor: pointer; text-decoration: none !important; }
.social-icon:hover { background: rgba(0, 242, 254, 0.1); border-color: rgba(0, 242, 254, 0.3); color: #00f2fe !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 242, 254, 0.2); text-decoration: none !important;}

.footer-links-container { display: flex; gap: 5rem; }
.footer-col { display: flex; flex-direction: column; gap: 12px; }
.footer-col-title { font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; }
.footer-link { font-size: 14px; color: #8892A4 !important; cursor: pointer; transition: all 0.2s; position: relative; width: fit-content; text-decoration: none !important; }
.footer-link:hover { color: #00f2fe !important; transform: translateX(2px); text-decoration: none !important; }

.footer-bottom { display: flex; justify-content: space-between; align-items: center; padding-top: 2rem; }
.footer-copy { font-size: 13px; color: #6b7280; }
.footer-bottom-links { display: flex; gap: 24px; align-items: center; }
.footer-bottom-link { font-size: 13px; color: #6b7280 !important; text-decoration: none !important; transition: color 0.2s; cursor: pointer; }
.footer-bottom-link:hover { color: #ffffff !important; text-decoration: none !important; }

@media (max-width: 900px) {
    .footer-top { flex-direction: column; }
    .footer-links-container { width: 100%; justify-content: space-between; gap: 2rem; }
    .footer-bottom { flex-direction: column; gap: 1rem; text-align: center; }
}

/* ============================================================ */
/* COMPREHENSIVE MOBILE RESPONSIVENESS                         */
/* ============================================================ */
@media (max-width: 768px) {
    /* === STREAMLIT COLUMN STACKING OVERRIDE =================== */
    /* Force ALL column layouts to stack vertically on mobile */
    div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    /* EXCEPT the navbar — keep that as a row */
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) {
        flex-direction: row !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"] {
        width: auto !important;
        flex: unset !important;
        min-width: unset !important;
    }
    /* Navbar: logo takes most space, auth area is compact */
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(1) {
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(2) {
        display: none !important;  /* hide nav links */
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(3) {
        flex: 0 0 auto !important;
        min-width: 0 !important;
    }

    /* === BLOCK CONTAINER ======================================= */
    .block-container {
        padding-top: 80px !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }

    /* === HERO SECTION ========================================== */
    .hero-wrapper { padding: 2rem 1rem 1rem 1rem !important; }
    .hero-title { font-size: 36px !important; letter-spacing: -1px !important; line-height: 1.1 !important; }
    .hero-sub { font-size: 15px !important; max-width: 100% !important; }
    .hero-stats { flex-direction: column !important; gap: 1.5rem !important; }
    .hero-badge { font-size: 10px !important; padding: 6px 12px !important; }

    /* === TICKER ================================================ */
    .ticker-track span:first-child { font-size: 30px !important; }

    /* === BENTO GRID ============================================ */
    .bento-grid { grid-template-columns: 1fr !important; }
    .card-large { grid-column: span 1 !important; grid-row: span 1 !important; }
    .card-large .bento-visual { min-height: 180px !important; }

    /* === SECTION HEADINGS ====================================== */
    .section-title { font-size: 24px !important; letter-spacing: -1px !important; }
    .section-sub { font-size: 13px !important; }

    /* === METRICS SECTION ======================================== */
    .metrics-section { padding: 4rem 0 !important; }
    .metrics-flex-row {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 2.5rem !important;
        margin-top: 2rem !important;
    }
    .m-val { font-size: 48px !important; }
    .m-lbl { font-size: 10px !important; letter-spacing: 2px !important; }

    /* === ACTIVITY CARDS ======================================== */
    .activity-row { grid-template-columns: 1fr !important; gap: 12px !important; margin-top: 3rem !important; }

    /* === FOOTER ================================================= */
    .footer { padding: 2rem 0.5rem 4rem 0.5rem !important; }
    .footer-card { padding: 1.5rem !important; border-radius: 16px !important; }
    .footer-watermark { font-size: 70px !important; bottom: 2% !important; }
    .footer-links-container { flex-direction: column !important; gap: 1.5rem !important; }
    .footer-bottom { flex-direction: column !important; gap: 1rem !important; text-align: center !important; }
    .footer-bottom-links { gap: 12px !important; }
}
</style>
"""

def render_navbar(logged_in=False, doctor_initial="Dr"):
    nav_css = """
    <style>
    /* Target the exact horizontal block containing the nav hook */
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) {
        position: fixed;
        top: 0; left: 0;
        width: 100vw;
        height: 72px;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255,255,255,0.05);
        z-index: 10000;
        padding: 0 4rem;
        align-items: center;
    }
    
    /* Push the main Streamlit container down to prevent header overlap */
    .block-container {
        padding-top: 90px !important;
    }
    
    /* Make Streamlit columns inside the nav ignore standard margin to align better */
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div {
        align-items: center;
        justify-content: center;
    }
    
    /* Always keep the navbar as a horizontal row */
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"] {
        flex: unset !important;
        min-width: unset !important;
    }
    
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) {
            padding: 0 0.75rem !important;
            height: 60px !important;
        }
        /* Navbar height on mobile */
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) {
            height: 60px !important;
        }
        /* Hide middle nav links column on mobile */
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(2) {
            display: none !important;
        }
        /* Logo column — stretch to fill remaining */
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(1) {
            flex: 1 1 auto !important;
        }
        /* Auth column — compact, don't wrap */
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) > div[data-testid="stColumn"]:nth-child(3) {
            flex: 0 0 auto !important;
            overflow: visible !important;
        }
        /* Make logo text slightly smaller */
        div[data-testid="stHorizontalBlock"]:has(.nav-hook) span[style*="font-size:24px"] {
            font-size: 18px !important;
        }
        /* shrink auth buttons on mobile */
        div.element-container:has(.nav-btn-login) + div.element-container button,
        div.element-container:has(.nav-btn-signup) + div.element-container button {
            padding: 3px 10px !important;
            font-size: 12px !important;
            min-height: 32px !important;
        }
    }

    /* Streamlit Page Links styled to look like custom nav */
    .stPageLink { margin: 0 !important; display: flex; justify-content: center; }
    .stPageLink a {
        padding: 8px 16px !important;
        border-radius: 8px !important;
        color: rgba(255,255,255,0.6) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        transition: all 0.2s !important;
        background: transparent !important;
    }
    .stPageLink a:hover {
        background: rgba(0, 242, 254, 0.1) !important;
        color: #fff !important;
    }

    /* Auth Buttons Styling using precise adjacent sibling selector to prevent global bleeding */
    div.element-container:has(.nav-btn-login) + div.element-container button {
        background: transparent !important;
        border: 1px solid rgba(0, 242, 254, 0.4) !important;
        border-radius: 8px !important;
        padding: 4px 16px !important;
        min-height: 38px !important;
        transition: all 0.3s !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div.element-container:has(.nav-btn-login) + div.element-container button p {
        color: #00f2fe !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        margin: 0 !important;
        font-size: 14px !important;
    }
    div.element-container:has(.nav-btn-login) + div.element-container button:hover {
        background: rgba(0, 242, 254, 0.1) !important;
        border-color: #00f2fe !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(0,242,254,0.15) !important;
    }

    div.element-container:has(.nav-btn-signup) + div.element-container button {
        background: #00f2fe !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 4px 16px !important;
        min-height: 38px !important;
        box-shadow: 0 4px 15px rgba(0,242,254,0.3) !important;
        transition: all 0.3s !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div.element-container:has(.nav-btn-signup) + div.element-container button p {
        color: #050505 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 800 !important;
        margin: 0 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
    }
    div.element-container:has(.nav-btn-signup) + div.element-container button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,242,254,0.5) !important;
        background: #33f5ff !important;
    }
    
    div.element-container:has(.nav-btn-logout) + div.element-container button {
        background: transparent !important;
        border: 1px solid rgba(255, 8, 68, 0.3) !important;
        border-radius: 8px !important;
        padding: 2px 12px !important;
        min-height: 32px !important;
        transition: all 0.2s !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div.element-container:has(.nav-btn-logout) + div.element-container button p {
        color: #ff0844 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        margin: 0 !important;
    }
    div.element-container:has(.nav-btn-logout) + div.element-container button:hover {
        background: rgba(255, 8, 68, 0.1) !important;
        border-color: #ff0844 !important;
    }

    /* Animations for logo ring */
    @keyframes spin-slow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes pulse-ring {
        0%, 100% { opacity: 1; border-color: rgba(0, 242, 254, 0.4); }
        50% { opacity: 0.4; border-color: rgba(0, 242, 254, 0.1); }
    }
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    # 3-column layout: Logo | Links | Auth
    col_logo, col_links, col_auth = st.columns([1.2, 2, 1], vertical_alignment="center")

    with col_logo:
        st.markdown('<div class="nav-hook"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; cursor:pointer;" onclick="window.location.href='/'">
          <div style="position: relative; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;">
              <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; border-radius: 50%; border: 2px solid transparent; border-top-color: #00f2fe; border-right-color: #00f2fe; animation: spin-slow 3s linear infinite;"></div>
              <div style="position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px; border-radius: 50%; border: 1px solid rgba(0, 242, 254, 0.4); animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;"></div>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position: relative; z-index: 10;">
                  <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
                  <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
              </svg>
          </div>
          <div style="display:flex; flex-direction:column; line-height:1;">
            <span style="font-size:24px; font-weight:800; color:#fff; letter-spacing:-1px;">NeuroTriage</span>
            <span style="font-size:14px; font-weight:800; color:#00f2fe; margin-top:2px;">AI</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_links:
        if logged_in:
            l1, l2, l3, l4, l5 = st.columns(5)
            with l1: st.page_link("pages/1_Dashboard.py", label="Dashboard")
            with l2: st.page_link("pages/2_New_Scan.py", label="New Scan")
            with l3: st.page_link("pages/3_Patient_History.py", label="History")
            with l4: st.page_link("pages/4_Batch_Upload.py", label="Batch")
            with l5: st.page_link("pages/5_Reports.py", label="Reports")
        else:
            # Anchor links for landing page
            st.markdown("""
            <div style="display:flex; justify-content:center; gap:2rem;">
               <a href="#features" style="color:rgba(255,255,255,0.6); text-decoration:none; font-size:14px; font-weight:500;">Features</a>
               <a href="#metrics" style="color:rgba(255,255,255,0.6); text-decoration:none; font-size:14px; font-weight:500;">Metrics</a>
               <a href="#footer" style="color:rgba(255,255,255,0.6); text-decoration:none; font-size:14px; font-weight:500;">About</a>
            </div>
            """, unsafe_allow_html=True)

    with col_auth:
        if logged_in:
            a1, a2 = st.columns([2, 1], vertical_alignment="center")
            with a1:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:12px; justify-content:flex-end;">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:6px;height:6px;background:#00f2fe;border-radius:50%;box-shadow:0 0 6px #00f2fe;"></div>
                        <span style="font-size:10px;color:rgba(255,255,255,0.6);letter-spacing:1px;font-weight:600;">LIVE</span>
                    </div>
                    <div style="width:36px;height:36px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#00f2fe;box-shadow:0 0 15px rgba(0,0,0,0.3);">{doctor_initial}</div>
                </div>
                """, unsafe_allow_html=True)
            with a2:
                # Add a container wrapper strictly for custom CSS targeting
                logout_container = st.container()
                with logout_container:
                    st.markdown('<div class="nav-btn-logout"></div>', unsafe_allow_html=True)
                    if st.button("Logout", key="nav_logout_btn"):
                        st.session_state["trigger_logout"] = True
                        st.rerun()
        else:
            a1, a2 = st.columns(2)
            with a1:
                login_container = st.container()
                with login_container:
                    st.markdown('<div class="nav-btn-login"></div>', unsafe_allow_html=True)
                    if st.button("Log In", key="nav_login_btn"):
                        st.session_state["trigger_auth"] = "login"
                        st.rerun()
            with a2:
                signup_container = st.container()
                with signup_container:
                    st.markdown('<div class="nav-btn-signup"></div>', unsafe_allow_html=True)
                    if st.button("Sign Up", key="nav_signup_btn"):
                        st.session_state["trigger_auth"] = "register"
                        st.rerun()

    # --- Mobile Bottom Navigation Bar (logged-in only) ---
    if logged_in:
        st.markdown("""
        <style>
        /* ============================================= */
        /* MOBILE BOTTOM NAV BAR                        */
        /* ============================================= */
        .mobile-bottom-nav {
            display: none;  /* hidden on desktop */
        }
        @media (max-width: 768px) {
            /* Show bottom nav on mobile */
            .mobile-bottom-nav {
                display: flex !important;
                position: fixed;
                bottom: 0; left: 0; right: 0;
                z-index: 9999;
                background: rgba(5, 5, 5, 0.95);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-top: 1px solid rgba(0, 242, 254, 0.15);
                padding: 8px 0 env(safe-area-inset-bottom, 8px);
                justify-content: space-around;
                align-items: center;
                gap: 0;
            }
            .mobile-nav-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 3px;
                padding: 4px 8px;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none !important;
                color: rgba(255,255,255,0.45) !important;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                transition: all 0.2s;
                flex: 1;
                max-width: 72px;
            }
            .mobile-nav-item:hover, .mobile-nav-item.active {
                color: #00f2fe !important;
            }
            .mobile-nav-icon {
                font-size: 20px;
                line-height: 1;
            }
            /* Push page content above the bottom bar */
            .block-container {
                padding-bottom: 80px !important;
            }
            /* hide the Streamlit default page link nav on mobile (bottom strip) */
            section[data-testid="stSidebarNav"] {
                display: none !important;
            }
        }
        </style>
        <nav class="mobile-bottom-nav" id="mobileBottomNav">
            <a class="mobile-nav-item" href="/1_Dashboard">
                <span class="mobile-nav-icon">📊</span>
                <span>Dashboard</span>
            </a>
            <a class="mobile-nav-item" href="/2_New_Scan">
                <span class="mobile-nav-icon">📸</span>
                <span>New Scan</span>
            </a>
            <a class="mobile-nav-item" href="/3_Patient_History">
                <span class="mobile-nav-icon">📁</span>
                <span>History</span>
            </a>
            <a class="mobile-nav-item" href="/4_Batch_Upload">
                <span class="mobile-nav-icon">📂</span>
                <span>Batch</span>
            </a>
            <a class="mobile-nav-item" href="/5_Reports">
                <span class="mobile-nav-icon">📄</span>
                <span>Reports</span>
            </a>
        </nav>
        <script>
        (function() {
            // Highlight the active page in the bottom nav
            var path = window.location.pathname;
            var items = document.querySelectorAll('.mobile-nav-item');
            items.forEach(function(item) {
                if (path && item.getAttribute('href') && path.toLowerCase().includes(item.getAttribute('href').replace('/', '').toLowerCase())) {
                    item.classList.add('active');
                    item.style.color = '#00f2fe';
                }
            });
        })();
        </script>
        """, unsafe_allow_html=True)

HERO_TOP_HTML = """
<div class="hero-badge"><div class="hero-badge-dot"></div> AI-Powered Clinical Tool</div>
<h1 class="hero-title">Detect Stroke.<br><span>Save Lives.</span><br>Instantly.</h1>
<p class="hero-sub">Upload a brain CT scan and get instant AI-powered stroke detection, ischemic lesion localisation, and a downloadable clinical report in seconds.</p>
"""

TICKER_HTML = """
<div class="ticker-wrap" style="width: 100vw; position: relative; left: 50%; margin-left: -50vw; background: transparent; border-top: 3px solid rgba(0, 242, 254, 0.3); border-bottom: 3px solid rgba(0, 242, 254, 0.3); overflow: hidden; padding: 2rem 0; margin-bottom: 4rem; display: flex; align-items: center; white-space: nowrap; box-shadow: 0 0 30px rgba(0,242,254,0.05);">
<div class="ticker-track" style="display: flex; gap: 8vw; width: max-content; animation: scrollTicker 15s linear infinite;">
<div style="display:flex; align-items:baseline; gap:12px;"><span style="color:#00f2fe; font-size:clamp(24px, 5vw, 48px); font-weight:800; letter-spacing:-1px;">93.1%</span><span style="color:#8892A4; font-size:clamp(12px, 2vw, 15px); font-weight:500;">Accuracy</span></div>
<div style="display:flex; align-items:baseline; gap:12px;"><span style="color:#00f2fe; font-size:clamp(24px, 5vw, 48px); font-weight:800; letter-spacing:-1px;">97.9%</span><span style="color:#8892A4; font-size:clamp(12px, 2vw, 15px); font-weight:500;">AUC Score</span></div>
<div style="display:flex; align-items:baseline; gap:12px;"><span style="color:#00f2fe; font-size:clamp(24px, 5vw, 48px); font-weight:800; letter-spacing:-1px;">&lt; 2s</span><span style="color:#8892A4; font-size:clamp(12px, 2vw, 15px); font-weight:500;">Latency</span></div>
<div style="display:flex; align-items:baseline; gap:12px;"><span style="color:#00f2fe; font-size:clamp(24px, 5vw, 48px); font-weight:800; letter-spacing:-1px;">24/7</span><span style="color:#8892A4; font-size:clamp(12px, 2vw, 15px); font-weight:500;">Support</span></div>
</div>
</div>
<style>
@keyframes scrollTicker {
0% { transform: translateX(0); }
100% { transform: translateX(-50%); }
}
.ticker-wrap:hover .ticker-track {
animation-play-state: paused;
}
</style>
"""

FEATURES_HTML = """
<div class="features-section" style="padding-top: 2rem;">
<div class="section-inner" style="max-width: 900px; margin: 0 auto; padding: 0 2rem;">
<h2 class="section-title" style="font-size: 42px; font-weight: 800; margin-bottom: 2rem; text-align: left; letter-spacing: -2px;">Comprehensive Platform</h2>

<div class="bento-grid">
<!-- 1. Large Top Left (Span 2x2) -->
<div class="bento-card card-large" style="cursor:pointer;" onclick="openFModal(this)" data-title="AI Stroke Detection" data-sub="Deep learning classification with 93.1% accuracy" data-desc="Our proprietary deep learning model achieves 93.1% accuracy in stroke detection with 97.9% AUC. Built on EfficientNet-B0 architecture and trained on thousands of clinical CT scans, it identifies ischemic strokes in real-time with exceptional precision." data-bens="Real-time stroke detection in under 2 seconds|93.1% accuracy with 97.9% AUC score|Reduces false positives by 40% compared to traditional methods|Integrates seamlessly with existing hospital PACS systems" data-specs="Model: EfficientNet-B0 with custom lesion-aware classification|Input: DICOM or standard image formats (JPG, PNG)|Output: Confidence score + clinical risk category|Processing time: < 2 seconds per scan">
<div class="bento-content">
<h3 class="bento-title">AI Stroke Detection</h3>
<p class="bento-desc">Deep learning classification with 93.1% accuracy</p>
</div>
<div class="bento-visual">
<div class="glow-bg" style="position:absolute; width:100%; height:100%; top:0; left:0; background:radial-gradient(circle at center, rgba(0,242,254,0.1), transparent 70%);"></div>
<img src=\"""" + IMG_WHISK + """\" style="width:100%; height:100%; object-fit:cover; position:relative; z-index:2; border-radius:12px; opacity:0.85; mix-blend-mode:screen;" />
</div>
</div>

<!-- 2. Small Top Right -->
<div class="bento-card" style="cursor:pointer;" onclick="openFModal(this)" data-title="Clinical Explainability" data-sub="Grad-CAM heatmaps show AI reasoning" data-desc="Explore critical findings through our interactive 3D viewer. We leverage Grad-CAM to overlay high-fidelity spatial heatmaps directly onto the DICOM slices, ensuring complete clinical transparency." data-bens="Real-time 3D rendering|Multi-planar reconstruction (MPR)|Measure lesion volumes dynamically|Toggle tissue density thresholds" data-specs="Render Engine: WebGL/Three.js|Latency: < 50ms interaction loop|Volumetric accuracy: 0.1 cubic mm">
<div class="bento-icon">⚡</div>
<div class="bento-content">
<h3 class="bento-title">Clinical Explainability</h3>
<p class="bento-desc">Grad-CAM heatmaps show AI reasoning</p>
</div>
</div>

<!-- 3. Small Middle Right -->
<div class="bento-card" style="cursor:pointer;" onclick="openFModal(this)" data-title="Batch Processing" data-sub="Process multiple scans simultaneously" data-desc="Built for high-volume diagnostic centers. Upload massive ZIP folders of CT series and our dynamic scheduling engine automatically allocates GPU resources to process them in parallel." data-bens="Unlimited queue scaling|Asynchronous background tasks|Automatic PDF generation map|Status webhooks integration" data-specs="Queue System: Native async pool|Max concurrent nodes: 124|Failover handling: Auto-retry on CUDA OOM">
<div class="bento-icon">📊</div>
<div class="bento-content">
<h3 class="bento-title">Batch Processing</h3>
<p class="bento-desc">Process multiple scans simultaneously</p>
</div>
</div>

<!-- 4. Small Bottom Left -->
<div class="bento-card" style="cursor:pointer;" onclick="openFModal(this)" data-title="Lesion Segmentation" data-sub="U-Net powered ischemic lesion localisation" data-desc="Pinpoint exact stroke regions using our advanced image segmentation overlays. It highlights specific borders of ischemic core and penumbra, enabling rapid clinical assessment of tissue at risk." data-bens="Pixel-perfect boundary generation|Contrast-independent mask creation|Supports diverse slice thickness levels" data-specs="Algorithm: 3D U-Net variant|Mask resolution: Native equivalent|IoU Score: 0.81 clinical benchmark">
<div class="bento-content">
<h3 class="bento-title">Lesion Segmentation</h3>
<p class="bento-desc">U-Net powered ischemic lesion localisation</p>
</div>
<div class="bento-visual" style="display:flex; align-items:center; justify-content:center; padding-top:1.5rem;">
<img src=\"""" + IMG_SEGMENTATION + """\" style="width:100%; height:100%; object-fit:contain; border-radius:8px; opacity:0.9; mix-blend-mode:screen;"/>
</div>
</div>

<!-- 5. Small Bottom Middle -->
<div class="bento-card" style="cursor:pointer;" onclick="openFModal(this)" data-title="Confidence-Based Triage" data-sub="Automatic risk stratification" data-desc="Our AI immediately assigns a confidence score to every processed scan. High-risk, actionable results instantly float to the top of your queue and can trigger webhooks to clinical pager systems." data-bens="Zero-delay SMS/Pager routing|Color-coded priority queueing|Customizable threshold triggers" data-specs="Risk logic: Multi-variate bayesian|Latency: Instant post-inference|Alert channels: SMS, Webhook, HL7">
<div class="bento-content">
<h3 class="bento-title">Confidence-Based Triage</h3>
<p class="bento-desc">Automatic risk stratification</p>
</div>
<div class="bento-visual" style="display:flex; align-items:center; justify-content:center; padding-top:1.5rem;">
<img src=\"""" + IMG_TRIAGE + """\" style="width:90%; height:90%; object-fit:contain; border-radius:8px; opacity:0.9; mix-blend-mode:screen;"/>
</div>
</div>

<!-- 6. Small Bottom Right -->
<div class="bento-card" style="cursor:pointer;" onclick="openFModal(this)" data-title="Automated Reporting" data-sub="Generate PDF reports at scale" data-desc="Replace manual transcriptions with one-click, HIPAA-compliant clinical reports. Our engine automatically structures metadata, DICOM header info, and AI prediction heatmaps into a clean PDF format." data-bens="Standardized clinical formatting|Embedded DICOM preview slices|Includes complete metadata extraction" data-specs="Generation Engine: Custom templating|Formats: PDF, JSON, HL7|Export support: Direct to EHR">
<div class="bento-icon">🕒</div>
<div class="bento-content">
<h3 class="bento-title">Automated Reporting</h3>
<p class="bento-desc">Generate PDF reports at scale</p>
</div>
</div>

</div>
</div>

<!-- Modal Injection -->
<div id="featModalCtx" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.85); backdrop-filter:blur(8px); z-index:9999; align-items:center; justify-content:center; padding:1rem;">
  <div style="background:#09090b; width:100%; max-width:600px; max-height:90vh; overflow-y:auto; border-radius:16px; border:1px solid rgba(0,242,254,0.3); box-shadow:0 10px 40px rgba(0,242,254,0.15); display:flex; flex-direction:column; animation:slideDown 0.3s ease-out;">
    <div style="padding:2rem 2rem 1.5rem 2rem; display:flex; justify-content:space-between; align-items:flex-start;">
      <div>
        <h2 id="fmTitle" style="color:#fff; font-size:28px; font-weight:800; margin:0 0 8px 0; letter-spacing:-1px;">Title</h2>
        <p id="fmSub" style="color:#8892A4; font-size:14px; margin:0;">Subtitle</p>
      </div>
      <button onclick="closeFModal()" style="background:transparent; border:1px solid rgba(0,242,254,0.3); color:#00f2fe; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:16px;">✕</button>
    </div>
    <div style="padding:0 2rem;">
      <div style="width:100%; height:200px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer;" class="bento-visual">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:8px;"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
        <span style="color:#8892A4; font-size:12px;">Click to play demo</span>
      </div>
    </div>
    <div style="padding:2rem;">
      <div style="margin-bottom:2rem;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          <span style="color:#fff; font-weight:700; font-size:16px;">Overview</span>
        </div>
        <p id="fmDesc" style="color:#8892A4; font-size:14px; line-height:1.6; margin:0;">Description</p>
      </div>
      <div style="margin-bottom:2rem;">
        <h4 style="color:#fff; font-weight:700; font-size:16px; margin:0 0 12px 0;">Key Benefits</h4>
        <ul id="fmBens" style="color:#8892A4; font-size:14px; line-height:1.8; margin:0; padding-left:1.2rem;"></ul>
      </div>
      <div>
        <h4 style="color:#fff; font-weight:700; font-size:16px; margin:0 0 12px 0;">Technical Specifications</h4>
        <div id="fmSpecs" style="display:flex; flex-direction:column; gap:8px;"></div>
      </div>
    </div>
    <div style="padding:1.5rem 2rem; padding-top:1rem; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; gap:16px;">
      <button onclick="closeFModal()" style="flex:1; padding:12px; background:transparent; border:1px solid rgba(255,255,255,0.1); color:#fff; border-radius:8px; font-weight:600; cursor:pointer;" class="btn-hover-glow">Close</button>
      <button style="flex:1; padding:12px; background:#00f2fe; border:none; color:#000; border-radius:8px; font-weight:700; cursor:pointer;" class="btn-hover-glow">Learn More</button>
    </div>
  </div>
</div>
<script>
function openFModal(el) {
  document.getElementById('fmTitle').innerText = el.getAttribute('data-title') || 'Title';
  document.getElementById('fmSub').innerText = el.getAttribute('data-sub') || 'Subtitle';
  document.getElementById('fmDesc').innerText = el.getAttribute('data-desc') || 'Overview';
  var b = el.getAttribute('data-bens');
  var bensHtml = '';
  if(b) b.split('|').forEach(function(i){ bensHtml += '<li>'+i+'</li>'; });
  document.getElementById('fmBens').innerHTML = bensHtml;
  var sp = el.getAttribute('data-specs');
  var specsHtml = '';
  if(sp) sp.split('|').forEach(function(i){ specsHtml += '<div style=\"padding:12px 16px; border:1px solid rgba(0,242,254,0.2); border-radius:8px; background:rgba(0,242,254,0.02); font-size:13px; color:#a3e0f0; font-family:monospace;\">'+i+'</div>'; });
  document.getElementById('fmSpecs').innerHTML = specsHtml;
  document.getElementById('featModalCtx').style.display = 'flex';
}
function closeFModal() {
  document.getElementById('featModalCtx').style.display = 'none';
}
</script>
</div>
"""

METRICS_HTML = """
<div id="metrics" class="metrics-section">
<div class="section-inner" style="position:relative; z-index: 10;">
<div class="section-tag" style="background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(4px);">Model Performance</div>
<h2 class="section-title" style="text-shadow: 0 4px 20px rgba(0,0,0,0.8);">Validated on real CT data</h2>
<p class="section-sub" style="text-shadow: 0 2px 10px rgba(0,0,0,0.8);">All metrics computed on held-out validation set</p>
<div class="metrics-flex-row">
<div class="metric-item">
<div class="m-val">90.4%</div>
<div class="m-lbl"><div class="m-dot dot-cyan"></div>Accuracy</div>
</div>
<div class="metric-item">
<div class="m-val">87.6%</div>
<div class="m-lbl"><div class="m-dot dot-cyan"></div>F1 Score</div>
</div>
<div class="metric-item">
<div class="m-val">96.8%</div>
<div class="m-lbl"><div class="m-dot dot-cyan"></div>AUC-ROC</div>
</div>
<div class="metric-item">
<div class="m-val">0.422</div>
<div class="m-lbl"><div class="m-dot dot-red"></div>Dice Score</div>
</div>
<div class="metric-item">
<div class="m-val">0.301</div>
<div class="m-lbl"><div class="m-dot dot-red"></div>IoU Score</div>
</div>
</div>
<div class="activity-row">
<div class="act-card">
<div class="act-header">
<div class="act-dot status-cyan"></div>
<div class="act-title">MODEL UPDATE</div>
</div>
<div class="act-desc">EfficientNet-B0 weights synchronized. Latest validation accuracy reached 90.4%.</div>
<div class="act-time">22:04:19 UTC</div>
</div>
<div class="act-card">
<div class="act-header">
<div class="act-dot status-cyan"></div>
<div class="act-title">INFERENCE PIPELINE</div>
</div>
<div class="act-desc">Batch processor latency optimized &lt;3s. GPU tensor allocation dynamic scaling active.</div>
<div class="act-time">21:58:33 UTC</div>
</div>
<div class="act-card">
<div class="act-header">
<div class="act-dot status-red"></div>
<div class="act-title">SYSTEM ALERT</div>
</div>
<div class="act-desc">DICOM processing node reached 85% memory capacity. Automatically spawning new instance.</div>
<div class="act-time">19:12:05 UTC</div>
</div>
<div class="act-card">
<div class="act-header">
<div class="act-dot status-purple"></div>
<div class="act-title">SECURITY AUDIT</div>
</div>
<div class="act-desc">Firebase Auth token rotation complete. All clinical data access logs successfully verified.</div>
<div class="act-time">14:00:22 UTC</div>
</div>
</div>
</div>
</div>
"""

FOOTER_HTML = """
<div id="footer" class="footer">
<div class="footer-watermark">NEUROTRIAGE</div>
<div class="footer-card">
<div class="footer-top">
<div class="footer-brand">
<div class="footer-brand-title">
<div style="display:flex; align-items:center; gap:12px;">
  <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; border-radius: 50%; border: 2px solid transparent; border-top-color: #00f2fe; border-right-color: #00f2fe; animation: spin-slow 3s linear infinite;"></div>
      <div style="position: absolute; top: 3px; left: 3px; right: 3px; bottom: 3px; border-radius: 50%; border: 1px solid rgba(0, 242, 254, 0.4); animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;"></div>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position: relative; z-index: 10;">
          <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
          <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
          <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>
          <path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>
          <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>
          <path d="M3.477 10.896a4 4 0 0 1 .585-.396"/>
          <path d="M19.938 10.5a4 4 0 0 1 .585.396"/>
          <path d="M6 18a4 4 0 0 1-1.967-.516"/>
          <path d="M19.967 17.484A4 4 0 0 1 18 18"/>
      </svg>
  </div>
<div style="display:flex; flex-direction:column; align-items:flex-start; line-height:1;">
  <span style="font-size:24px; font-weight:800; color:#fff; letter-spacing:-1px;">NeuroTriage</span>
  <span style="font-size:14px; font-weight:800; color:#00f2fe; margin-top:2px;">AI</span>
</div>
</div>
</div>
<div class="footer-brand-desc">
NeuroTriage empowers clinical teams to transform raw CT data into clear, actionable, and rapid insights — saving critical time when every second counts for stroke patients.
</div>
<div class="footer-socials">
<a class="social-icon">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l11.733 16h4.267l-11.733 -16z" /><path d="M4 20l6.768 -6.768m2.46 -2.46l6.772 -6.772" /></svg>
</a>
<a class="social-icon">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
</a>
<a class="social-icon">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
</a>
<a class="social-icon">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
</a>
</div>
</div>

<div class="footer-links-container">
<div class="footer-col">
<div class="footer-col-title">Product</div>
<a class="footer-link">Features</a>
<a class="footer-link">Pricing</a>
<a class="footer-link">Integrations</a>
<a class="footer-link">Changelog</a>
</div>
<div class="footer-col">
<div class="footer-col-title">Resources</div>
<a class="footer-link">Documentation</a>
<a class="footer-link">Tutorials</a>
<a class="footer-link">Blog</a>
<a class="footer-link">Support</a>
</div>
<div class="footer-col">
<div class="footer-col-title">Company</div>
<a class="footer-link">About</a>
<a class="footer-link">Careers</a>
<a class="footer-link">Contact</a>
<a class="footer-link">Partners</a>
</div>
</div>
</div>

<div class="footer-bottom">
<div class="footer-copy">© 2026 NeuroTriage AI. All rights reserved. Do not use for standalone clinical diagnosis.</div>
<div class="footer-bottom-links">
<a class="footer-bottom-link">Privacy Policy</a>
<a class="footer-bottom-link">Terms of Service</a>
<a class="footer-bottom-link">Cookies Settings</a>
</div>
</div>
</div>
</div>
"""

THREE_JS_IFRAME = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; padding: 0; overflow: hidden; background: transparent; display: flex; align-items: center; justify-content: center; height: 100vh; position: relative;}
  .brain-container { width: 100%; height: 100%; position: relative; z-index: 10; display: flex; align-items: center; justify-content: center; transform: translateY(-5%);}
  
  /* SVG Dashed Lines (Orbiting rings) */
  .svg-lines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5; pointer-events: none; }
  path, circle { stroke-linecap: round; transform-origin: center; }
  @keyframes rotateLines { 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

  <!-- Dynamic Orbiting Dashed Rings -->
  <svg class="svg-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
    <circle cx="50" cy="50" r="35" stroke-dasharray="2 6" stroke-width="0.3" stroke="rgba(0, 242, 254, 0.5)" fill="none" style="animation: rotateLines 20s linear infinite;"/>
    <circle cx="50" cy="50" r="25" stroke-dasharray="1 4" stroke-width="0.2" stroke="rgba(255, 255, 255, 0.3)" fill="none" style="animation: rotateLines 15s linear infinite reverse;"/>
    <circle cx="50" cy="50" r="45" stroke-dasharray="4 12" stroke-width="0.2" stroke="rgba(255, 255, 255, 0.1)" fill="none" style="animation: rotateLines 25s linear infinite;"/>
  </svg>

  <div class="brain-container" id="three-container"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
  const container = document.getElementById('three-container');
  const width = container.clientWidth;
  const height = container.clientHeight;
  
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.z = 8.5; camera.position.y = 1;

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
  renderer.setSize(width, height);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);
  
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.enableZoom = false; 
  controls.autoRotate = true;  
  controls.autoRotateSpeed = 2.0;

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  
  const pointLight = new THREE.PointLight(0x00f2fe, 1.0, 100);
  pointLight.position.set(2, 3, 5);
  scene.add(pointLight);

  let brainModel = null;
  const loader = new THREE.GLTFLoader();

  loader.load('https://res.cloudinary.com/dyuxgmjf1/image/upload/v1774984064/ai-brain_cpdtp3.glb', function (gltf) {
      brainModel = gltf.scene;
      
      const hologramMaterial = new THREE.MeshBasicMaterial({ 
          color: 0x00f2fe, 
          wireframe: true, 
          transparent: true, 
          opacity: 0.15 
      });
      const solidCoreMaterial = new THREE.MeshPhongMaterial({
          color: 0x001122,
          transparent: true,
          opacity: 0.6,
          shininess: 100
      });

      brainModel.traverse(function (child) {
          if (child.isMesh) {
              const wireMesh = new THREE.Mesh(child.geometry, hologramMaterial);
              const coreMesh = new THREE.Mesh(child.geometry, solidCoreMaterial);
              wireMesh.scale.set(1.02, 1.02, 1.02);
              child.parent.add(wireMesh);
              child.material = coreMesh.material;
          }
      });

      const box = new THREE.Box3().setFromObject(brainModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 5.0 / maxDim;
      
      const group = new THREE.Group();
      group.add(brainModel);
      
      group.scale.set(scale, scale, scale);
      group.position.sub(center.multiplyScalar(scale));
      group.rotation.x = 0.26;
      scene.add(group);
  });

  function animate() {
      requestAnimationFrame(animate);
      controls.update(); 
      renderer.render(scene, camera);
  }
  animate();
</script>
</body>
</html>
"""
