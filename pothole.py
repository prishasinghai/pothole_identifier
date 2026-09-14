"""
CivicTrust Platform - "Don't just mark it resolved. Prove it."
 
A Streamlit port of the original HTML/JS ticket-verification page.
Run with:
    pip install streamlit --break-system-packages
    streamlit run civictrust_app.py
"""
 
import datetime as dt
import streamlit as st
import folium
from streamlit_folium import st_folium
 
# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(page_title="CivicTrust Platform", page_icon="✓", layout="centered")
 
# --------------------------------------------------------------------------
# Session state (mirrors the JS globals: status, audit log, questions, notes)
# --------------------------------------------------------------------------
def init_state():
    defaults = {
        "status": "pending",  # pending | verified | flagged
        "citizen_note": (
            "Deep pothole on right lane causing vehicle tire damage "
            "and traffic slowdowns."
        ),
        "worker_note": (
            "Cold-mix asphalt poured, compacted with heavy roller, "
            "and leveled with road surface."
        ),
        "before_img": None,
        "after_img": None,
        "questions": [
            {
                "author": "Resident #402",
                "time": "02:10 PM",
                "text": "Was traffic diverted while Crew #4 worked on this road patch?",
            }
        ],
        "audit_log": [
            {
                "time": "10:15 AM",
                "message": "Complaint submitted by Citizen (ID: #USER-3921). Ticket opened.",
                "warning": False,
            }
        ],
        "result_alert": None,  # ("success"|"error", message)
        "hotspots": [
            {
                "id": "TK-8042",
                "title": "Severe Pothole - 5th Ave & Main St",
                "lat": 40.7128,
                "lon": -74.0060,
                "status": "pending",
            },
            {
                "id": "TK-7911",
                "title": "Cracked Sidewalk - Elm St",
                "lat": 40.7145,
                "lon": -74.0090,
                "status": "verified",
            },
            {
                "id": "TK-8033",
                "title": "Broken Streetlight - 2nd & Oak",
                "lat": 40.7102,
                "lon": -74.0021,
                "status": "flagged",
            },
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
 
 
def add_log_entry(message: str, warning: bool = False):
    st.session_state.audit_log.append(
        {
            "time": dt.datetime.now().strftime("%I:%M %p"),
            "message": message,
            "warning": warning,
        }
    )
 
 
def approve_ticket():
    st.session_state.status = "verified"
    st.session_state.result_alert = (
        "success",
        "Thank you! Resolution verified. Ticket is officially closed and archived.",
    )
    add_log_entry("Citizen verified proof. Ticket status locked to VERIFIED RESOLVED.")
 
 
def flag_ticket(reason: str):
    reason_text = f'Reason: "{reason}"' if reason.strip() else "No specific reason provided."
    st.session_state.status = "flagged"
    st.session_state.result_alert = (
        "error",
        f"Flagged! Ticket has been reopened. {reason_text} "
        f"An alert has been recorded against Crew #4.",
    )
    add_log_entry(f"FLAG ALERT: Citizen reported false proof. {reason_text}", warning=True)
 
 
def sync_main_ticket_pin():
    """Keep the map pin for TK-8042 in step with the ticket's current status."""
    for spot in st.session_state.hotspots:
        if spot["id"] == "TK-8042":
            spot["status"] = st.session_state.status
 
 
def add_hotspot(title: str, lat: float, lon: float):
    title = title.strip()
    if not title:
        st.warning("Please describe the issue first!")
        return
    new_id = f"TK-{8000 + len(st.session_state.hotspots) + 1}"
    st.session_state.hotspots.append(
        {"id": new_id, "title": title, "lat": lat, "lon": lon, "status": "pending"}
    )
    add_log_entry(f'New bad spot reported on map: "{title}" ({new_id}).')
 
 
def post_question(text: str):
    text = text.strip()
    if not text:
        st.warning("Please type a question first!")
        return
    st.session_state.questions.insert(
        0,
        {
            "author": "Citizen (You)",
            "time": "Just Now",
            "text": text,
        },
    )
    add_log_entry(f'Public Question Raised: "{text}"')
 
 
# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
init_state()
 
# ---- Header ----
header_l, header_r = st.columns([4, 1])
with header_l:
    st.markdown("## ✓ CivicTrust Platform")
    st.caption("Don't just mark it resolved. Prove it.")
with header_r:
    st.markdown(
        "<div style='text-align:right;padding-top:20px;'>"
        "<span style='background:#0ea5e91a;color:#38bdf8;border:1px solid #0ea5e933;"
        "padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;'>"
        "Public Audit Mode</span></div>",
        unsafe_allow_html=True,
    )
st.divider()
 
# ---- Ticket summary ----
with st.container(border=True):
    st.markdown("`TICKET #TK-8042`  ·  Category: Infrastructure / Road Maintenance")
    st.markdown("### Severe Pothole on 5th Avenue & Main St")
    st.caption("Location: Downtown District • Reported by: Anonymous Citizen")
 
    status_map = {
        "pending": ("⏳ PENDING CITIZEN PROOF VERIFICATION", "orange"),
        "verified": ("✅ VERIFIED & OFFICIALLY CLOSED", "green"),
        "flagged": ("🚨 REOPENED - FALSE RESOLUTION FLAGGED", "red"),
    }
    label, color = status_map[st.session_state.status]
    st.markdown(f":{color}[**{label}**]")
 
sync_main_ticket_pin()
 
# ---- Area map with marked bad spots ----
with st.container(border=True):
    st.markdown("### 🗺️ Area Map — Reported Bad Spots")
    st.caption("All open, verified, and flagged issues in the downtown district.")
 
    pin_color = {"pending": "orange", "verified": "green", "flagged": "red"}
    pin_icon = {"pending": "exclamation-sign", "verified": "ok-sign", "flagged": "warning-sign"}
 
    center_lat = sum(s["lat"] for s in st.session_state.hotspots) / len(st.session_state.hotspots)
    center_lon = sum(s["lon"] for s in st.session_state.hotspots) / len(st.session_state.hotspots)
 
    area_map = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB dark_matter")
 
    for spot in st.session_state.hotspots:
        folium.Marker(
            location=[spot["lat"], spot["lon"]],
            tooltip=f"{spot['id']} — {spot['title']}",
            popup=folium.Popup(
                f"<b>{spot['id']}</b><br>{spot['title']}<br>"
                f"Status: <b>{spot['status'].upper()}</b>",
                max_width=250,
            ),
            icon=folium.Icon(
                color=pin_color.get(spot["status"], "blue"),
                icon=pin_icon.get(spot["status"], "info-sign"),
            ),
        ).add_to(area_map)
 
    st_folium(area_map, width=None, height=380, key="area_map")
 
    legend_cols = st.columns(3)
    legend_cols[0].markdown("🟠 **Pending verification**")
    legend_cols[1].markdown("🟢 **Verified / closed**")
    legend_cols[2].markdown("🔴 **Flagged false resolution**")
 
    with st.expander("📍 Report a new bad spot on the map"):
        new_title = st.text_input("Issue description", placeholder="e.g., 'Fallen tree blocking bike lane'")
        lat_col, lon_col = st.columns(2)
        with lat_col:
            new_lat = st.number_input("Latitude", value=center_lat, format="%.6f")
        with lon_col:
            new_lon = st.number_input("Longitude", value=center_lon, format="%.6f")
        if st.button("Add to map"):
            add_hotspot(new_title, new_lat, new_lon)
            st.rerun()
 
# ---- Before / After comparison ----
col_before, col_after = st.columns(2)
 
with col_before:
    with st.container(border=True):
        st.markdown("**📷 1. CITIZEN REPORT (BEFORE)**")
        st.caption("Sep 11, 2026 - 10:15 AM")
 
        before_file = st.file_uploader(
            "Upload Before Photo", type=["png", "jpg", "jpeg", "webp"], key="before_upload"
        )
        if before_file is not None:
            st.session_state.before_img = before_file
            add_log_entry("New Before photo uploaded by citizen.")
 
        if st.session_state.before_img is not None:
            st.image(st.session_state.before_img, use_container_width=True)
        else:
            st.info("📁 No Before Photo Uploaded")
 
        st.session_state.citizen_note = st.text_area(
            "Citizen Note / Problem Description:",
            value=st.session_state.citizen_note,
            height=80,
            key="citizen_note_input",
        )
 
with col_after:
    with st.container(border=True):
        st.markdown("**📷 2. WORKER SUBMISSION (AFTER)**")
        st.caption("Sep 11, 2026 - 03:40 PM")
 
        after_file = st.file_uploader(
            "Upload Worker After Photo", type=["png", "jpg", "jpeg", "webp"], key="after_upload"
        )
        if after_file is not None:
            st.session_state.after_img = after_file
            add_log_entry("New resolution proof photo uploaded by worker.")
 
        if st.session_state.after_img is not None:
            st.image(st.session_state.after_img, use_container_width=True)
        else:
            st.info("📁 No Resolution Proof Uploaded")
