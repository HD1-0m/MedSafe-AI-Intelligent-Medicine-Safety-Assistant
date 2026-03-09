import json
import streamlit as st
from PIL import Image

from core.ai_engine import AIEngine
from core.interaction_checker import InteractionChecker
from core.ocr_module import extract_prescription_raw_text, is_tesseract_available
from core.risk_engine import RiskEngine
from core.side_effect_engine import SideEffectEngine


def render_severity_badge(severity: str) -> None:
    color_map = {"HIGH": "#DC2626", "MEDIUM": "#F59E0B", "LOW": "#16A34A"}
    color = color_map.get(severity, "#64748B")
    st.markdown(
        f"""
        <div style="
            padding:10px 16px;
            border-radius:8px;
            background-color:{color};
            color:white;
            font-weight:600;
            display:inline-block;
            margin-bottom:10px;">
            Severity: {severity}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_card(title: str, content: str) -> None:
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(180deg, #0f172a 0%, #0b1220 100%);
            border:1px solid #334155;
            padding:20px;
            border-radius:12px;
            margin-top:15px;">
            <b style="color:#4ade80;">{title}</b>
            <hr style="border:1px solid #1E293B;">
            <div style="color:#cbd5e1; white-space:pre-wrap;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="MedSafe AI - Intelligent Medicine Safety Assistant",
    page_icon="🏥",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(1200px 500px at 10% -10%, #1f2937 0%, #0f172a 40%, #020617 100%);
        color: #e2e8f0;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, .stCaption {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid #1e293b;
    }
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background: #0b1220;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 6px;
    }
    button[data-baseweb="tab"] {
        border-radius: 10px !important;
        background: #0f172a !important;
        color: #94a3b8 !important;
        border: 1px solid #1e293b !important;
    }
    button[aria-selected="true"][data-baseweb="tab"] {
        background: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #ef4444 !important;
    }
    .stButton button {
        background: #059669 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
        background: #020817 !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    .stFileUploader {
        background: rgba(30, 41, 59, 0.45);
        border: 1px dashed #334155;
        border-radius: 12px;
        padding: 10px;
    }
    .block-container {
        padding-top: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_engines():
    return {
        "checker": InteractionChecker(),
        "risk": RiskEngine(),
        "ai": AIEngine(),
        "side": SideEffectEngine(),
    }


engines = get_engines()
if "selected_meds" not in st.session_state:
    st.session_state.selected_meds = []
if "last_interactions" not in st.session_state:
    st.session_state.last_interactions = []

st.title("🏥 MedSafe AI")
st.markdown("### Intelligent Medicine Safety Assistant")
st.caption("Educational tool only. This app does not provide diagnosis or treatment.")
st.divider()

st.sidebar.title("Navigation")
st.sidebar.subheader("AI Connection")
if st.sidebar.button("Check AI API Connection"):
    ok, message = engines["ai"].check_api_connection()
    if ok:
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)

tab_interactions, tab_ocr, tab_symptoms, tab_side, tab_emergency = st.tabs(
    [
        "Medicine Interaction Checker",
        "Prescription OCR",
        "Symptom & Doubt Solver",
        "Side-Effect Monitor",
        "Emergency Risk Predictor",
    ]
)

with tab_interactions:
    st.header("💊 Medicine Interaction Checker")
    meds_input = st.text_input(
        "Enter medicines (comma separated)",
        placeholder="e.g. Aspirin, Warfarin, Ibuprofen",
    )

    if st.button("Check Interactions", use_container_width=True):
        raw_input_names = [m.strip() for m in meds_input.split(",") if m.strip()]
        identified, unknown = engines["checker"].identify_medicines_from_text(meds_input)
        st.session_state.selected_meds = identified
        interactions = engines["checker"].check_interactions(identified)
        st.session_state.last_interactions = interactions

        if identified:
            st.subheader("Identified Medicines")
            for med in identified:
                st.write(f"- **{med['name']}** ({med['salt']})")
        else:
            st.info("No medicines identified from your input.")

        if interactions:
            st.subheader("Detected Interactions")
            descriptions = []
            for inter in interactions:
                descriptions.append(inter["description"])
                render_severity_badge(inter["risk"])
                st.write(f"**Pair:** {inter['pair'][0]} + {inter['pair'][1]}")
                st.write(f"**Description:** {inter['description']}")

            with st.spinner("Generating AI guidance..."):
                guidance = engines["ai"].explain_risk(interactions[0]["risk"], descriptions)
            render_ai_card("🤖 AI Enhanced Advice", guidance)
        elif identified:
            st.success("No known interactions detected for the selected medicines.")

        # AI fallback for unknown medicines or when DB has no interaction match.
        if len(raw_input_names) >= 2 and (unknown or not interactions):
            with st.spinner("Running AI fallback for broader interaction coverage..."):
                fallback = engines["ai"].analyze_unknown_interactions(raw_input_names)
            st.subheader("AI Fallback Interaction Analysis")
            fallback_interactions = fallback.get("interactions", [])
            if fallback_interactions:
                risk_priority = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
                top_risk = max(
                    (str(item.get("risk", "LOW")).upper() for item in fallback_interactions),
                    key=lambda x: risk_priority.get(x, 1),
                )
                render_severity_badge(top_risk)
                for inter in fallback_interactions:
                    st.write(f"**Pair:** {inter['pair'][0]} + {inter['pair'][1]}")
                    st.write(f"**Risk:** {inter['risk']}")
                    st.write(f"**Description:** {inter['description']}")
                    st.markdown("---")
            else:
                st.info("No strong interaction signal returned by AI fallback for the provided medicines.")

            render_ai_card("🤖 AI Fallback Safety Advice", fallback.get("advice", ""))

with tab_ocr:
    st.header("📄 Extract Medicines From Prescription")
    if not is_tesseract_available():
        st.error(
            "Tesseract OCR engine is not detected. Install Tesseract and set TESSERACT_CMD in .env "
            "if needed (Windows example: C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
        )
    uploaded_file = st.file_uploader(
        "Upload prescription image",
        type=["jpg", "jpeg", "png"],
        key="prescription_uploader",
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Prescription", use_container_width=True)

        if st.button("Process Prescription", use_container_width=True):
            with st.spinner("Extracting and analyzing prescription..."):
                image_bytes = uploaded_file.getvalue()
                clean_text = extract_prescription_raw_text(image_bytes)
                if clean_text:
                    st.subheader("Raw OCR Text (Tesseract)")
                    st.code(clean_text)
                    parsed_result = engines["ai"].parse_prescription_from_image(
                        image_bytes=image_bytes,
                        mime_type=getattr(uploaded_file, "type", "") or "image/png",
                        ocr_text=clean_text,
                    )
                    try:
                        parsed_json = json.loads(parsed_result)
                        if isinstance(parsed_json, dict) and parsed_json.get("reconstructed_text"):
                            st.subheader("Reconstructed Text (AI + Image)")
                            st.code(parsed_json["reconstructed_text"])
                        if isinstance(parsed_json, dict):
                            readable_text = engines["ai"].prescription_to_readable_text(
                                parsed_prescription=parsed_json,
                                raw_ocr_text=clean_text,
                            )
                            st.subheader("Readable Prescription (AI)")
                            st.write(readable_text)
                    except Exception:
                        render_ai_card("🤖 AI Structured Prescription Analysis", parsed_result)
                else:
                    st.error("Could not extract text. Please upload a clearer image.")

with tab_symptoms:
    st.header("💬 Symptom & Doubt Solver")
    symptoms_input = st.text_area(
        "Describe symptoms or ask a medical doubt",
        placeholder="e.g. I have mild fever and headache after taking antibiotics. What should I monitor?",
        height=180,
    )

    if st.button("Get AI Advice", use_container_width=True):
        if not symptoms_input.strip():
            st.warning("Please enter symptoms or a medical question.")
        else:
            symptom_tokens = [token.strip() for token in symptoms_input.split(",") if token.strip()]
            if not symptom_tokens:
                symptom_tokens = [symptoms_input.strip()]
            risk_result = engines["risk"].evaluate_risk(symptom_tokens, st.session_state.last_interactions)
            render_severity_badge(risk_result["severity"])
            for reason in risk_result["reasons"]:
                st.write(f"- {reason}")

            with st.spinner("Generating AI symptom guidance..."):
                advice = engines["ai"].solve_symptoms(symptoms_input, risk_result)
            render_ai_card("🤖 AI Symptom Guidance", advice)

with tab_side:
    st.header("⚠️ Experience & Side-Effect Monitor")
    age = st.number_input("Age", min_value=0, max_value=120, value=25)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    meds_taken = st.text_area("Medicines taken (comma separated)", height=100)
    doses = st.text_area("Doses taken in mg (comma separated)", height=100)
    experience = st.text_area(
        "What did you feel after taking medicines? (optional but recommended)",
        height=120,
    )

    if st.button("Monitor Side Effects", use_container_width=True):
        identified_meds, unknown = engines["checker"].identify_medicines_from_text(meds_taken)
        dose_values = [d.strip() for d in doses.split(",") if d.strip()]

        if unknown:
            st.warning(f"Not identified: {', '.join(unknown)}")
        if not identified_meds:
            st.warning("No valid medicines identified. Please enter at least one known medicine.")
        else:
            analysis = engines["side"].analyze(
                age=age,
                gender=gender,
                medicines=identified_meds,
                doses=dose_values,
                experience=experience,
            )
            render_severity_badge(analysis["risk_level"])
            st.subheader("Contributing Factors")
            for reason in analysis["reasons"]:
                st.write(f"- {reason}")
            st.info(f"Precaution: {analysis['precaution']}")

            with st.spinner("Generating AI side-effect guidance..."):
                advice = engines["ai"].monitor_side_effects(
                    age=age,
                    gender=gender,
                    medicines=[m["name"] for m in identified_meds],
                    doses=dose_values,
                    experience=experience,
                    rule_assessment=analysis,
                )
            render_ai_card("🤖 AI Side-Effect Analysis", advice)

with tab_emergency:
    st.header("🚨 Emergency Risk Predictor")
    emergency_symptoms = st.text_area(
        "Current emergency symptoms",
        placeholder="e.g. chest pain, severe shortness of breath, fainting",
        height=140,
    )
    medical_history = st.text_area(
        "Brief medical history",
        placeholder="e.g. hypertension, diabetes, previous heart disease",
        height=140,
    )

    if st.button("Predict Risk Level", use_container_width=True):
        if not emergency_symptoms.strip():
            st.warning("Please enter current symptoms first.")
        else:
            emergency_result = engines["risk"].evaluate_emergency_risk(
                emergency_symptoms, medical_history
            )
            render_severity_badge(emergency_result["severity"])
            st.subheader("Emergency Indicators")
            for reason in emergency_result["reasons"]:
                st.write(f"- {reason}")

            with st.spinner("Generating AI emergency guidance..."):
                emergency_advice = engines["ai"].predict_emergency_risk(
                    emergency_symptoms, medical_history, emergency_result
                )
            render_ai_card("🤖 AI Emergency Risk Analysis", emergency_advice)

st.divider()
st.caption(
    "Disclaimer: MedSafe AI is an educational tool and does not provide medical diagnosis or "
    "professional advice. Always consult with a qualified healthcare professional."
)
