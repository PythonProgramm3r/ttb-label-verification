import streamlit as st
import asyncio
import base64
from openai import AsyncOpenAI
import json

# 1. PAGE CONFIG & UI LOCKDOWN
st.set_page_config(page_title="TTB Label Verification System", page_icon="🍷", layout="wide")

# CSS Hack to physically remove the "Browse files" button, forcing drag-and-drop
st.markdown("""
    <style>
        [data-testid="stFileUploaderDropzone"] button {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. GOVERNMENT OFFICIAL BANNER
st.error("🏛️ **U.S. DEPARTMENT OF THE TREASURY — OFFICIAL USE ONLY**\n\nUnauthorized access, distribution, or misuse of this TTB Internal Compliance Portal is strictly prohibited under federal law.")

st.title("🍷 Alcohol and Tobacco Tax and Trade Bureau Label Verification System")
st.info("**Assessor Note:** To evaluate a batch of labels, please highlight your files and **Drag and Drop** them directly into the gray zone below. (The manual file browser is disabled for batch security protocols).")

# 3. SECURE BACKEND CONNECTION
try:
    # Pulling keys silently from the Streamlit Cloud backend
    api_key = st.secrets["AZURE_API_KEY"]
    azure_endpoint = st.secrets["AZURE_ENDPOINT"]
    deployment_name = st.secrets["AZURE_DEPLOYMENT"]
except KeyError:
    st.error("System Error: Secure Azure credentials not found in environment.")
    st.stop()

# Initialize the client securely using the new Foundry v1 structure
client = AsyncOpenAI(
    api_key=api_key,
    base_url=azure_endpoint,
    default_query={"api-version": "2024-10-21"}
)

# 4. TTB RULES CHECKLIST (SYSTEM PROMPT)
ttb_rules = """
You are a TTB (Alcohol and Tobacco Tax and Trade Bureau) Compliance Auditor. 
Analyze the provided alcohol label image and evaluate it against the following rules. 
Output your exact findings in this JSON format strictly:
{
  "brand_name": "Pass" or "Fail",
  "class_type": "Pass" or "Fail",
  "abv_present": "Pass" or "Fail",
  "net_contents": "Pass" or "Fail",
  "gov_warning_exact": "Pass" or "Fail",
  "notes": "Any brief explanatory notes or missing items."
}

Rules:
1. Brand name must be clearly stated.
2. Class/Type (e.g., Vodka, Bourbon, Wine) must be stated.
3. Alcohol by Volume (ABV) must be present.
4. Net contents (e.g., 750ml) must be present.
5. The Government Warning must be exact and present (if legible).
"""

# 5. ASYNC PROCESSING FUNCTIONS
async def process_label(image_bytes, filename, sem):
    async with sem:
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            response = await client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": ttb_rules
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Audit this label."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            return filename, response.choices[0].message.content, None
        except Exception as e:
            return filename, None, str(e)

async def run_batch(uploaded_files, max_workers=15):
    sem = asyncio.Semaphore(max_workers)
    tasks = []
    
    for file in uploaded_files:
        image_bytes = file.getvalue()
        tasks.append(process_label(image_bytes, file.name, sem))
        
    return await asyncio.gather(*tasks)

# 6. FRONTEND UPLOADER & EXECUTION
uploaded_files = st.file_uploader(
    "Drop label images or entire directory here", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🚀 Run Compliance Verification", type="primary"):
        with st.spinner(f"Auditing {len(uploaded_files)} labels..."):
            
            # Run the async batch process
            results = asyncio.run(run_batch(uploaded_files))
            
            total = len(results)
            approved = 0
            rejected = 0
            parsed_results = []
            
            for filename, result_json, error in results:
                if error:
                    parsed_results.append((filename, "REJECTED", f"Processing Error: {error}"))
                    rejected += 1
                else:
                    try:
                        data = json.loads(result_json)
                        # Check if all keys (excluding notes) are "Pass"
                        is_pass = all(v == "Pass" for k, v in data.items() if k != "notes")
                        if is_pass:
                            approved += 1
                            status = "APPROVED"
                        else:
                            rejected += 1
                            status = "REJECTED"
                        parsed_results.append((filename, status, data))
                    except:
                        rejected += 1
                        parsed_results.append((filename, "REJECTED", "Failed to parse JSON response."))
            
            st.divider()
            
            # Summary Metrics
            st.markdown("### 📊 Summary Results")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Processed", total)
            col2.metric("Approved", approved)
            col3.metric("Rejected", rejected)
            
            st.divider()
            
            # Detailed Breakdown
            st.markdown("### 🔍 Detailed Audit Breakdown")
            for filename, status, details in parsed_results:
                status_color = "🟢" if status == "APPROVED" else "🔴"
                with st.expander(f"{status_color} {filename} — Status: {status}"):
                    c1, c2 = st.columns([1, 2])
                    
                    with c1:
                        # Display the image using the updated syntax
                        matched_file = next((f for f in uploaded_files if f.name == filename), None)
                        if matched_file:
                            st.image(matched_file, caption=filename, width="stretch")
                    
                    with c2:
                        if isinstance(details, str):
                            st.error(details)
                        else:
                            st.markdown("#### Rules Checklist")
                            for key, val in details.items():
                                if key != "notes":
                                    icon = "✅" if val == "Pass" else "❌"
                                    st.markdown(f"* **{key.replace('_', ' ').title()}:** {icon} {val}")
                            
                            st.markdown("#### Notes")
                            st.info(details.get("notes", "No additional notes provided."))
