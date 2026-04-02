import sys
import os

# --- PATH RESOLUTION FIX ---
# Force Python to look in the local 'app' directory FIRST before site-packages
# This prevents our local 'utils' folder from colliding with 'cv2.utils'
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import streamlit as st
import requests
from dotenv import load_dotenv
from firebase_config import db, auth
from firebase_utils import log_action
from datetime import datetime
from landing_ui import (
    LANDING_CSS, HERO_TOP_HTML, TICKER_HTML,
    FEATURES_HTML, METRICS_HTML, FOOTER_HTML, THREE_JS_IFRAME,
    get_features_html, render_navbar
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NeuroTriage AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BASE DIR ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- LOAD CSS THEME ---
def load_css(file_path):
    if not os.path.isabs(file_path):
        file_path = os.path.join(BASE_DIR, file_path)
    with open(file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("assets/style.css")

# --- ENVIRONMENT VARIABLES ---
load_dotenv(override=True)

# Read FIREBASE_WEB_API_KEY from st.secrets (Streamlit Cloud) or .env (local)
try:
    FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", os.getenv("FIREBASE_WEB_API_KEY", ""))
except Exception:
    FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "user_uid" not in st.session_state:
    st.session_state["user_uid"] = ""
if "doctor_name" not in st.session_state:
    st.session_state["doctor_name"] = ""
if "trigger_auth" not in st.session_state:
    st.session_state["trigger_auth"] = None
if "trigger_logout" not in st.session_state:
    st.session_state["trigger_logout"] = False

# --- FIREBASE REST AUTH FUNCTIONS ---
def auth_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    return response.json()

def register_user(email, password, name):
    # 1. Create User via REST API
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    data = response.json()
    
    # 2. If successful, save profile to Firestore
    if "localId" in data:
        uid = data["localId"]
        doc_ref = db.collection("doctors").document(uid)
        doc_ref.set({
            "name": name,
            "email": email,
            "uid": uid,
            "created_at": datetime.now().isoformat()
        })
    return data

def get_doctor_name(uid):
    if db is None:
        return ""
    try:
        doc_ref = db.collection("doctors").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("name", "")
    except Exception:
        pass
    return ""

@st.dialog("System Authentication")
def show_auth_dialog(default_tab="login"):
    titles = ["Secure Login", "Create Account"] if default_tab == "login" else ["Create Account", "Secure Login"]
    tabs = st.tabs(titles)
    
    tab_login = tabs[0] if default_tab == "login" else tabs[1]
    tab_register = tabs[1] if default_tab == "login" else tabs[0]
    
    with tab_login:
        with st.form("login_form"):
            login_email = st.text_input("Dr. Email", placeholder="dr.smith@hospital.com")
            login_pass = st.text_input("Password", type="password")
            submitted_login = st.form_submit_button("Login to Dashboard")
            
            if submitted_login:
                if not FIREBASE_WEB_API_KEY or FIREBASE_WEB_API_KEY == "your_web_api_key_here":
                    st.error("FIREBASE_WEB_API_KEY is not set in .env")
                else:
                    with st.spinner("Authenticating..."):
                        res = auth_user(login_email, login_pass)
                        if "idToken" in res:
                            st.session_state["logged_in"] = True
                            st.session_state["user_email"] = login_email
                            st.session_state["user_uid"] = res["localId"]
                            # Try Firestore name first, then Auth displayName, then email
                            name = get_doctor_name(res["localId"])
                            if not name:
                                name = res.get("displayName", "")
                            if not name:
                                name = login_email.split("@")[0].replace(".", " ").title()
                            st.session_state["doctor_name"] = name
                            st.session_state["user_display_name"] = name
                            log_action(st.session_state["user_uid"], "login")
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(res.get("error", {}).get("message", "Authentication Failed"))

    with tab_register:
        with st.form("register_form"):
            reg_name = st.text_input("Full Name", placeholder="Dr. John Smith")
            reg_email = st.text_input("Email", placeholder="dr.smith@hospital.com")
            reg_pass = st.text_input("Password", type="password")
            submitted_register = st.form_submit_button("Register Account")
            
            if submitted_register:
                if not FIREBASE_WEB_API_KEY:
                    st.error("FIREBASE_WEB_API_KEY is not set in .env")
                elif not reg_name:
                    st.error("Please provide your full name.")
                else:
                    with st.spinner("Registering..."):
                        res = register_user(reg_email, reg_pass, reg_name)
                        if "idToken" in res:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error(res.get("error", {}).get("message", "Registration Failed"))

# --- AUTH/LOGOUT ACTION HANDLERS ---
if st.session_state.get("trigger_auth"):
    auth_mode = st.session_state.get("trigger_auth")
    st.session_state["trigger_auth"] = None
    show_auth_dialog(default_tab=auth_mode)

if st.session_state.get("trigger_logout"):
    uid = st.session_state.get("user_uid")
    if uid:
        log_action(uid, "logout")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- LOGIN / REGISTER VIEW ---
if not st.session_state["logged_in"]:
    # 1. Inject the Massive Custom UI CSS
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    # 2. Render Sticky Full-Width Python Navbar
    render_navbar(logged_in=False)
    
    # Add negative margin trick to full-bleed sections in CSS override
    st.markdown("""
    <style>
    .features-section, .metrics-section, .footer {
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
    }
    .stTabs {
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- AMBIENT PARTICLE CANVAS & CURSOR GLOW ---
    st.markdown("""
<style>
.particle-canvas {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    pointer-events: none; z-index: 0; overflow: hidden;
}
.particle {
    position: absolute; width: 2px; height: 2px;
    background: rgba(0, 242, 254, 0.4); border-radius: 50%;
    animation: particleDrift linear infinite;
}
@keyframes particleDrift {
    0% { transform: translateY(100vh) scale(0); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(-20vh) scale(1); opacity: 0; }
}
.cursor-glow {
    position: fixed; width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0, 242, 254, 0.03) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none; z-index: 1;
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s;
    transform: translate(-50%, -50%);
    opacity: 0;
}
/* On mobile, hide the cursor glow dot itself since touch shows a finger pulse instead */
@media (max-width: 768px) {
    .cursor-glow { width: 200px; height: 200px; }
}
</style>
<div class="particle-canvas" id="particleField"></div>
<div class="cursor-glow" id="cursorGlow"></div>
<script>
(function() {
    // Spawn particles
    const field = document.getElementById('particleField');
    if (field && !field.hasChildNodes()) {
        for (let i = 0; i < 40; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.left = Math.random() * 100 + 'vw';
            p.style.animationDuration = (12 + Math.random() * 20) + 's';
            p.style.animationDelay = (Math.random() * 15) + 's';
            p.style.width = (1 + Math.random() * 2) + 'px';
            p.style.height = p.style.width;
            p.style.opacity = 0.1 + Math.random() * 0.4;
            field.appendChild(p);
        }
    }
    // Cursor / touch glow
    const glow = document.getElementById('cursorGlow');
    if (glow) {
        // Desktop: mouse move
        document.addEventListener('mousemove', function(e) {
            glow.style.left = e.clientX + 'px';
            glow.style.top = e.clientY + 'px';
            glow.style.opacity = '1';
        });
        document.addEventListener('mouseleave', function() {
            glow.style.opacity = '0';
        });
        // Mobile: touch move (shows glow at touch point)
        document.addEventListener('touchmove', function(e) {
            const t = e.touches[0];
            glow.style.left = t.clientX + 'px';
            glow.style.top = t.clientY + 'px';
            glow.style.opacity = '0.8';
        }, { passive: true });
        document.addEventListener('touchend', function() {
            glow.style.opacity = '0';
        }, { passive: true });
    }
})();
</script>
    """, unsafe_allow_html=True)

    # 3. Hero Section - Responsive with mobile viewport detection
    import streamlit.components.v1 as components
    st.markdown("""
    <style>
    /* On mobile: stack hero columns */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:has(.hero-left-hook) {
            flex-direction: column !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.hero-left-hook) > div[data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        /* reduce 3D brain iframe size on mobile */
        div[data-testid="stHorizontalBlock"]:has(.hero-left-hook) > div[data-testid="stColumn"]:nth-child(2) iframe {
            height: 300px !important;
        }
        /* shrink the Secure Dashboard button on mobile */  
        div[data-testid="stHorizontalBlock"]:has(.hero-left-hook) .stButton button {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="cinematic-wrapper" style="margin-top:-2rem;">', unsafe_allow_html=True)
    
    hero_left, hero_right = st.columns([1.2, 1], gap="large")
    
    with hero_left:
        st.markdown('<div class="hero-left-hook"></div>', unsafe_allow_html=True)
        st.markdown(HERO_TOP_HTML, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Secure Dashboard", type="primary", use_container_width=False):
            st.session_state["trigger_auth"] = "login"
            st.rerun()
            
    with hero_right:
        components.html(THREE_JS_IFRAME, height=450, scrolling=False)
        
    st.markdown('</div>', unsafe_allow_html=True)
                                
    # 4. Render the continuous horizontal ticker
    st.markdown(TICKER_HTML, unsafe_allow_html=True)

    st.markdown('<div id="features" style="height:0;"></div>', unsafe_allow_html=True)
    # 5. Render the Bento Grid with interactive JS modals via components.html()
    # height=1400 fits desktop 3-col layout; the sendHeight JS inside auto-resizes for mobile
    components.html(get_features_html(), height=1400, scrolling=False)
    st.markdown(METRICS_HTML, unsafe_allow_html=True)
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# --- AUTHENTICATED MAIN VIEW ---
else:
    # 1. Hide the sidebar since we use the sleek top navbar
    st.markdown("""<style>[data-testid="stSidebar"] {display: none !important;}</style>""", unsafe_allow_html=True)

    # 2. Define pages and setup navigation FIRST so st.page_link knows about them
    pages = {
        "Menu": [
            st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/2_New_Scan.py", title="New Scan", icon="📸"),
            st.Page("pages/3_Patient_History.py", title="Patient History", icon="📁"),
            st.Page("pages/4_Batch_Upload.py", title="Batch Upload", icon="📂"),
            st.Page("pages/5_Reports.py", title="Reports", icon="📄")
        ]
    }
    
    # position="hidden" prevents the default sidebar from rendering the nav
    pg = st.navigation(pages, position="hidden")

    # 3. Now render the navbar (which uses st.page_link)
    initial = st.session_state.get("doctor_name", "")
    if initial:
        initial = initial[0].upper()
    else:
        # Fallback to email first char
        email = st.session_state.get("user_email", "")
        initial = email[0].upper() if email else "U"

    render_navbar(logged_in=True, doctor_initial=initial)

    # 4. Finally, run the selected page
    pg.run()
