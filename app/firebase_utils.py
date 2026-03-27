"""
firebase_utils.py — shared helper utilities for Firestore operations.
"""
import datetime
import streamlit as st
from firebase_config import db


def log_action(doctor_uid: str, action: str, patient_name: str = "", details: str = "") -> None:
    """
    Write an audit log entry to the 'audit_logs' Firestore collection.

    Args:
        doctor_uid:   UID of the authenticated doctor.
        action:       Short action code, e.g. 'login', 'scan_analyzed', 'pdf_downloaded'.
        patient_name: (optional) Patient name involved in the action.
        details:      (optional) Any extra free-text context.
    """
    try:
        db.collection("audit_logs").add({
            "doctor_uid":   doctor_uid,
            "action":       action,
            "patient_name": patient_name,
            "details":      details,
            "timestamp":    datetime.datetime.utcnow().isoformat(),
        })
        # Temporary debug toast
        # st.toast(f"✅ Audit logged: {action}", icon="✅")
    except Exception as e:
        # Surface the error directly in the UI for debugging
        st.toast(f"❌ Audit log failed: {e}", icon="❌")
        print(f"[firebase_utils] log_action failed: {e}")
