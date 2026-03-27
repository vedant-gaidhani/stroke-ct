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
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "user_uid" not in st.session_state:
    st.session_state["user_uid"] = ""
if "doctor_name" not in st.session_state:
    st.session_state["doctor_name"] = ""

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
    doc_ref = db.collection("doctors").document(uid)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("name", "Doctor")
    return "Doctor"

# --- LOGIN / REGISTER VIEW ---
if not st.session_state["logged_in"]:
    st.title("🧠 NeuroTriage AI")
    st.subheader("AI-Powered Stroke Detection System")
    
    tab_login, tab_register = st.tabs(["Login", "Register"])
    
    with tab_login:
        st.markdown("### Doctor Login")
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="dr.smith@hospital.com")
            login_pass = st.text_input("Password", type="password")
            submitted_login = st.form_submit_button("Login")
            
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
                            st.session_state["doctor_name"] = get_doctor_name(res["localId"])
                            log_action(st.session_state["user_uid"], "login")
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(res.get("error", {}).get("message", "Authentication Failed"))

    with tab_register:
        st.markdown("### Create Account")
        with st.form("register_form"):
            reg_name = st.text_input("Full Name", placeholder="Dr. John Smith")
            reg_email = st.text_input("Email", placeholder="dr.smith@hospital.com")
            reg_pass = st.text_input("Password", type="password")
            submitted_register = st.form_submit_button("Register")
            
            if submitted_register:
                if not FIREBASE_WEB_API_KEY or FIREBASE_WEB_API_KEY == "your_web_api_key_here":
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

# --- AUTHENTICATED MAIN VIEW ---
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"## 🩺 Dr. {st.session_state['doctor_name']}")
        st.caption(f"{st.session_state['user_email']}")
        st.markdown("---")
        
        # --- LOGOUT ---
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True, type="primary"):
            uid = st.session_state.get("user_uid")
            if uid:
                log_action(uid, "logout")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
    # --- NAVIGATION ---
    pages = {
        "Menu": [
            st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/2_New_Scan.py", title="New Scan", icon="📸"),
            st.Page("pages/3_Patient_History.py", title="Patient History", icon="📁"),
            st.Page("pages/4_Batch_Upload.py", title="Batch Upload", icon="📂"),
            st.Page("pages/5_Reports.py", title="Reports", icon="📄")
        ]
    }
    
    pg = st.navigation(pages)
    
    # Title is set conditionally based on the page to avoid duplicating if the page sets its own
    # but as a fallback/global header:
    # st.title("🧠 NeuroTriage AI")
    # st.subheader("AI-Powered Stroke Detection System", divider="green")
    
    pg.run()
