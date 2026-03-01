import streamlit as st
from PIL import Image
from core.ocr_module import extract_text_from_image, clean_ocr_text
from core.interaction_checker import InteractionChecker
from core.risk_engine import RiskEngine
from core.ai_engine import AIEngine
from utils.helpers import log_event

# Page Configuration
st.set_page_config(
    page_title="MedSafe AI - Healthcare Safety",
    page_icon="🏥",
    layout="wide"
)

# Initialize Engines
@st.cache_resource
def get_engines():
    return {
        "checker": InteractionChecker(),
        "risk": RiskEngine(),
        "ai": AIEngine()
    }

engines = get_engines()

# Header
st.title("🏥 MedSafe AI")
st.markdown("### Your Intelligent Healthcare Safety Companion")
st.divider()

# Sidebar
st.sidebar.title("Navigation")
tab_selection = st.sidebar.radio(
    "Go to",
    ["Medicine Interaction Checker", "Prescription OCR", "Symptom Risk Evaluation"]
)

# Tab 1: Medicine Interaction Checker
if tab_selection == "Medicine Interaction Checker":
    st.header("🔍 Medicine Interaction Checker")
    st.write("Check for potential interactions between multiple medicines.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        search_query = st.text_input("Search and Add Medicine (e.g., Aspirin, Warfarin)")
        if st.button("Add to List"):
            med = engines['checker'].identify_medicine(search_query)
            if med:
                if 'selected_meds' not in st.session_state:
                    st.session_state.selected_meds = []
                
                if med['name'] not in [m['name'] for m in st.session_state.selected_meds]:
                    st.session_state.selected_meds.append(med)
                    st.success(f"Added: {med['name']}")
                else:
                    st.warning("Medicine already in list.")
            else:
                st.error("Medicine not found in database.")

    with col2:
        st.subheader("Selected Medicines")
        if 'selected_meds' in st.session_state and st.session_state.selected_meds:
            for i, med in enumerate(st.session_state.selected_meds):
                st.write(f"- **{med['name']}** ({med['salt']})")
            
            if st.button("Clear List"):
                st.session_state.selected_meds = []
                st.rerun()
        else:
            st.info("No medicines selected.")

    if 'selected_meds' in st.session_state and len(st.session_state.selected_meds) > 1:
        st.divider()
        st.subheader("Interaction Analysis")
        interactions = engines['checker'].check_interactions(st.session_state.selected_meds)
        
        if interactions:
            for inter in interactions:
                color = "red" if inter['risk'] == "HIGH" else "orange"
                st.markdown(f"#### ⚠️ Risk: :{color}[{inter['risk']}]")
                st.write(f"**Pair:** {inter['pair'][0]} + {inter['pair'][1]}")
                st.write(f"**Description:** {inter['description']}")
                
                # AI Explanation
                with st.expander("View AI Explanation"):
                    risk_data = {"severity": inter['risk'], "reasons": [inter['description']]}
                    explanation = engines['ai'].generate_explanation(risk_data)
                    st.write(explanation)
        else:
            st.success("No known interactions detected between selected medicines.")

# Tab 2: Prescription OCR
elif tab_selection == "Prescription OCR":
    st.header("📄 Prescription OCR & AI Parsing")
    st.write("Upload a prescription image to extract and analyze medicine details.")
    
    uploaded_file = st.file_uploader("Choose a prescription image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Prescription', use_container_width=True)
        
        if st.button("Process Prescription"):
            with st.spinner("Extracting text..."):
                raw_text = extract_text_from_image(image)
                clean_text = clean_ocr_text(raw_text)
                
                if clean_text:
                    st.subheader("Extracted Text")
                    st.code(clean_text)
                    
                    with st.spinner("AI Parsing..."):
                        parsed_result = engines['ai'].parse_prescription(clean_text)
                        st.subheader("AI Structured Analysis")
                        st.write(parsed_result)
                else:
                    st.error("Could not extract text from the image. Please ensure the image is clear.")

# Tab 3: Symptom Risk Evaluation
elif tab_selection == "Symptom Risk Evaluation":
    st.header("🚨 Symptom Risk Evaluation")
    st.write("Evaluate health risk based on symptoms and current medications.")
    
    symptoms_input = st.text_area("Enter symptoms (separated by commas, e.g., chest pain, dizziness)")
    
    if st.button("Evaluate Risk"):
        if symptoms_input:
            symptoms_list = [s.strip() for s in symptoms_input.split(",")]
            
            # Check for interactions if medicines are selected
            interactions = []
            if 'selected_meds' in st.session_state:
                interactions = engines['checker'].check_interactions(st.session_state.selected_meds)
            
            risk_result = engines['risk'].evaluate_risk(symptoms_list, interactions)
            
            severity = risk_result['severity']
            color = "red" if severity == "HIGH" else ("orange" if severity == "MEDIUM" else "green")
            
            st.markdown(f"## Overall Severity: :{color}[{severity}]")
            
            st.subheader("Evaluation Details")
            for reason in risk_result['reasons']:
                st.write(f"- {reason}")
                
            if severity == "HIGH":
                st.error("🚨 **IMMEDIATE ACTION REQUIRED:** Please consult a doctor or emergency services immediately.")
            
            with st.expander("View AI Educational Guidance"):
                explanation = engines['ai'].generate_explanation(risk_result)
                st.write(explanation)
        else:
            st.warning("Please enter at least one symptom.")

# Footer
st.divider()
st.caption("Disclaimer: MedSafe AI is an educational tool and does not provide medical diagnosis or professional advice. Always consult with a healthcare professional.")
