import streamlit as st
import requests

st.set_page_config(page_title="AI Transformation Project", layout="wide")
st.title("AI Transformation Project")

backend_url = "http://127.0.0.1:8000"

# Initialize Session State variables for text inputs
if "org_name" not in st.session_state:
    st.session_state["org_name"] = ""
if "industry" not in st.session_state:
    st.session_state["industry"] = ""
if "challenge" not in st.session_state:
    st.session_state["challenge"] = ""

uploaded_file = st.file_uploader(
    "Upload Organization Documents (PDF, TXT, DOCX)",
    type=["pdf", "txt", "docx"]
)

# Parse uploaded file and populate input fields
if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    try:
        response = requests.post(f"{backend_url}/upload", files=files)
        if response.status_code == 200:
            extracted_text = response.json().get("extracted_text", "")
            
            # Simple text parsing for structured text files
            for line in extracted_text.split("\n"):
                clean_line = line.strip()
                if clean_line.lower().startswith("organization name:"):
                    st.session_state["org_name"] = clean_line.split(":", 1)[1].strip()
                elif clean_line.lower().startswith("industry:"):
                    st.session_state["industry"] = clean_line.split(":", 1)[1].strip()
                elif clean_line.lower().startswith("challenge:"):
                    st.session_state["challenge"] = clean_line.split(":", 1)[1].strip()

            st.success("File processed! Input fields auto-filled below.")
    except Exception as e:
        st.error(f"Upload failed: {e}")

# Form Inputs bound to session state
col1, col2, col3 = st.columns(3)
with col1:
    org_name = st.text_input("Organization Name", key="org_name", placeholder="e.g. Apex Retailers")
with col2:
    industry = st.text_input("Industry", key="industry", placeholder="e.g. Retail")
with col3:
    challenge = st.text_input("Challenge", key="challenge", placeholder="e.g. Declining foot traffic")

if st.button("Analyze Organization", type="primary"):
    if not org_name.strip() or not industry.strip() or not challenge.strip():
        st.warning("Please fill in Organization Name, Industry, and Challenge before running analysis.")
    else:
        payload = {"org_name": org_name, "industry": industry, "challenge": challenge}
        
        with st.spinner("Analyzing organization and retrieving intelligence..."):
            try:
                response = requests.post(f"{backend_url}/analyze", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    analysis = data.get("analysis", {})

                    tabs = st.tabs([
                        "Business Situation", "External Change", "Strategic Issues",
                        "Opportunities", "Priorities", "Initiatives", "Outcomes"
                    ])

                    with tabs[0]:
                        st.write(analysis.get("situation", ""))

                    with tabs[1]:
                        st.write(analysis.get("external_change", ""))
                        st.subheader("Supporting Evidence & Sources")
                        sources = analysis.get("sources", [])
                        
                        if sources:
                            for src in sources:
                                if isinstance(src, dict):
                                    title = src.get("title", src.get("url", "Link"))
                                    url = src.get("url", "#")
                                    st.markdown(f"- [{title}]({url})")
                                elif isinstance(src, str):
                                    st.markdown(f"- [{src}]({src})")
                        else:
                            st.info("No sources available for this analysis.")

                    with tabs[2]:
                        st.write(analysis.get("strategic_issues", ""))

                    with tabs[3]:
                        st.write(analysis.get("opportunities", ""))

                    with tabs[4]:
                        st.write(analysis.get("priorities", ""))
                        with st.expander("Impact/Effort Matrix"):
                            st.table({
                                "Priority": ["AI adoption", "Customer engagement"],
                                "Impact": ["High", "Medium"],
                                "Effort": ["Medium", "High"]
                            })

                    with tabs[5]:
                        st.write(analysis.get("initiatives", ""))

                    with tabs[6]:
                        st.write(analysis.get("outcomes", ""))
                else:
                    st.error(f"Backend status error: {response.status_code}")
            except Exception as e:
                st.error(f"Failed to communicate with backend server: {e}")