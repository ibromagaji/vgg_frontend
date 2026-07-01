import streamlit as st
from pathlib import Path
import requests
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LeafScan · Plant Diagnostics",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
css = Path("style.css").read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "upload"          # "upload" | "result"
if "prediction" not in st.session_state:
    st.session_state.prediction = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — calls EC2 API and parses response
# ══════════════════════════════════════════════════════════════════════════════
def run_model(image_bytes: bytes) -> dict:
    resp = requests.post(
        "http://vgg-ec2.duckdns.org/predict",
        files={"file": ("image.jpg", image_bytes)},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    disease_name = data["prediction"]
    info = json.loads(data["disease_info"])

    return {
        "disease":     disease_name.replace("_", " "),
        "description": info["description"],
        "symptoms":    info["symptoms"],
        "treatment":   info["treatment"],
        "prevention":  info["prevention"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
def page_upload():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="header-block">
      <h1 class="brand-title">LeafScan</h1>
      <p class="brand-subtitle">Plant Disease Classifier.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload Dropzone ───────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        label="Upload plant specimen",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded:
        st.markdown(
            f'<p class="file-metadata">Selected: {uploaded.name} ({uploaded.size / 1024:.1f} KB)</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="file-metadata-placeholder">Supported formats: JPG, PNG, WEBP</p>', unsafe_allow_html=True)

    # ── Action Button ─────────────────────────────────────────────────────────
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    predict_clicked = st.button(
        "Run Diagnostics",
        disabled=uploaded is None,
        key="predict_btn",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Elegant Loading & Execution ──────────────────────────────────────────
    if predict_clicked and uploaded:
        # Replaces the page with a clean, high-end loading container
        st.markdown("""
        <div class="loading-overlay">
          <div class="pulse-loader"></div>
          <p class="loading-text">Deconstructing cellular patterns...</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner(""):
            try:
                result = run_model(uploaded.getvalue())
            except Exception as e:
                st.error(f"Could not reach the model server: {e}")
                st.stop()

        st.session_state.prediction = result
        st.session_state.uploaded_image = uploaded.getvalue()
        st.session_state.page = "result"
        st.rerun()

    # # ── Guidelines ────────────────────────────────────────────────────────────
    # st.markdown("""
    # <div class="guidelines-grid">
    #   <div class="guide-item"><span>01 /</span> Clear lighting reveals surface structural details</div>
    #   <div class="guide-item"><span>02 /</span> Frame primarily the symptom or affected leaf area</div>
    #   <div class="guide-item"><span>03 /</span> Keep the camera parallel to the leaf surface</div>
    # </div>
    # """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def page_result():
    pred = st.session_state.prediction
    img  = st.session_state.uploaded_image

    # ── Top Navigation ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nav-bar">
      <span class="nav-brand">LeafScan</span>
      <span class="nav-status">Diagnostic Summary</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Split Grid: Visual vs Profile ─────────────────────────────────────────
    col_img, col_desc = st.columns([1, 1.2], gap="large")

    with col_img:
        if img:
            st.markdown('<div class="result-frame">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_desc:
        st.markdown(f"""
        <div class="diagnosis-profile">
          <span class="label-caps">Identified Condition</span>
          <h2 class="condition-title">{pred["disease"]}</h2>
          <p class="condition-body">{pred["description"]}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Tri-Panel Action Plan ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3, gap="medium")
    panels = [
        ("Clinical Symptoms", pred["symptoms"]),
        ("Immediate Treatment", pred["treatment"]),
        ("Long-term Prevention", pred["prevention"]),
    ]

    for col, (title, items) in zip([c1, c2, c3], panels):
        items_html = "".join(f'<li>{i}</li>' for i in items)
        col.markdown(f"""
        <div class="manifest-card">
          <h4 class="manifest-title">{title}</h4>
          <ul class="manifest-list">{items_html}</ul>
        </div>
        """, unsafe_allow_html=True)

    # ── Footer Return Button ──────────────────────────────────────────────────
    st.markdown('<div class="return-container">', unsafe_allow_html=True)
    if st.button("New Analysis", key="back_btn"):
        st.session_state.page = "upload"
        st.session_state.prediction = None
        st.session_state.uploaded_image = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "upload":
    page_upload()
else:
    page_result()