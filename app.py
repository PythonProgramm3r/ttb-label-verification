import asyncio
import base64
import json
import os
from typing import List, Dict, Any
import streamlit as st
from openai import AsyncAzureOpenAI

# ------------------------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="TTB Label Verification Portal",
    page_icon="🍷",
    layout="wide"
)

# ------------------------------------------------------------------------------
# SYSTEM PROMPT
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an expert TTB (Alcohol and Tobacco Tax and Trade Bureau) Compliance Agent. 
Your task is to verify that the information on the provided alcohol label image matches regulatory requirements and standard submission criteria.

### VALIDATION RULES

1. STRICT MATCHING (The Government Warning)
The Government Warning must be verified character-by-character:
- The phrase "GOVERNMENT WARNING:" MUST be entirely uppercase and bold/prominent.
- The warning text following the colon must be legible, unobstructed, and complete.

2. FUZZY MATCHING (Brand Name, Class/Type, Net Contents, ABV)
- Ignore minor layout differences or casing variations in brand names.
- Verify that standard required elements (Brand Name, Class/Type, ABV statement, Net Contents) are present on the visual label.

### OUTPUT FORMAT
You MUST respond ONLY with a raw JSON object (no markdown, no ```json blocks) formatted as follows:

{
  "status": "APPROVED" | "REJECTED",
  "checks": {
    "brand_name": true | false,
    "class_type": true | false,
    "abv_present": true | false,
    "net_contents": true | false,
    "government_warning_exact": true | false
  },
  "notes": "Brief explanation of any failed checks or optical anomalies."
}
"""

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def encode_image_to_base64(uploaded_file) -> str:
    """Reads uploaded file bytes and converts to base64 string."""
    bytes_data = uploaded_file.getvalue()
    return base64.b64encode(bytes_data).decode("utf-8")

async def analyze_single_label(
    client: AsyncAzureOpenAI,
    deployment_name: str,
    uploaded_file,
    semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """Processes a single label asynchronously using Azure OpenAI GPT-4o."""
    async with semaphore:
        try:
            base64_image = encode_image_to_base64(uploaded_file)
            
            response = await client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Verify this alcohol label image against TTB compliance requirements."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{uploaded_file.type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.0
            )

            raw_text = response.choices[0].message.content.strip()
            # Clean possible markdown formatting if returned
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "").strip()

            parsed_result = json.loads(raw_text)
            parsed_result["filename"] = uploaded_file.name
            return parsed_result

        except Exception as e:
            return {
                "filename": uploaded_file.name,
                "status": "REJECTED",
                "checks": {
                    "brand_name": False,
                    "class_type": False,
                    "abv_present": False,
                    "net_contents": False,
                    "government_warning_exact": False
                },
                "notes": f"Processing Error: {str(e)}"
            }

async def process_batch_concurrently(
    azure_endpoint: str,
    api_key: str,
    deployment_name: str,
    api_version: str,
    files: List[Any],
    concurrency_limit: int = 10
) -> List[Dict[str, Any]]:
    """Orchestrates parallel execution across uploaded files."""
    client = AsyncAzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version
    )
    
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = [
        analyze_single_label(client, deployment_name, file, semaphore) 
        for file in files
    ]
    return await asyncio.gather(*tasks)

# ------------------------------------------------------------------------------
# SIDEBAR / CONFIGURATION
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ Azure Settings")
azure_endpoint = st.sidebar.text_input("Azure OpenAI Endpoint", value=os.getenv("AZURE_OPENAI_ENDPOINT", ""))
api_key = st.sidebar.text_input("API Key", value=os.getenv("AZURE_OPENAI_API_KEY", ""), type="password")
deployment_name = st.sidebar.text_input("Deployment Name", value="gpt-4o-prototype")
api_version = st.sidebar.text_input("API Version", value="2024-02-15-preview")
concurrency_limit = st.sidebar.slider("Parallel Processing Workers", min_value=1, max_value=30, value=15)

# ------------------------------------------------------------------------------
# MAIN DASHBOARD
# ------------------------------------------------------------------------------
st.title("🍷 TTB Label Verification System")
st.markdown("Upload batch directories or multiple label images to instantly evaluate compliance rules.")

uploaded_files = st.file_uploader(
    "Drop label images or entire directory here",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files="directory" # <--- The magic string that enables folder uploads
)

if uploaded_files:
    st.info(f"📁 {len(uploaded_files)} file(s) loaded and ready for analysis.")
    
    if st.button("🚀 Run Compliance Verification", type="primary"):
        if not azure_endpoint or not api_key or not deployment_name:
            st.error("Please configure your Azure Endpoint, API Key, and Deployment Name in the sidebar.")
        else:
            with st.spinner(f"Verifying {len(uploaded_files)} labels concurrently..."):
                # Execute async batch
                results = asyncio.run(
                    process_batch_concurrently(
                        azure_endpoint=azure_endpoint,
                        api_key=api_key,
                        deployment_name=deployment_name,
                        api_version=api_version,
                        files=uploaded_files,
                        concurrency_limit=concurrency_limit
                    )
                )

            # Calculate summary stats
            total = len(results)
            approved = sum(1 for r in results if r.get("status") == "APPROVED")
            rejected = total - approved

            st.divider()
            st.header("📊 Summary Results")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Processed", total)
            col2.metric("Approved", approved, delta=f"{(approved/total)*100:.1f}%")
            col3.metric("Rejected", rejected, delta=f"-{(rejected/total)*100:.1f}%", delta_color="inverse")

            st.divider()
            st.header("🔍 Detailed Audit Breakdown")

            for result in results:
                status = result.get("status", "REJECTED")
                filename = result.get("filename", "Unknown File")
                checks = result.get("checks", {})
                notes = result.get("notes", "No additional notes.")

                status_icon = "🟢" if status == "APPROVED" else "🔴"
                
                with st.expander(f"{status_icon} **{filename}** — Status: **{status}**"):
                    c1, c2 = st.columns([1, 2])
                    
                    with c1:
                        # Find matching file object to display thumbnail
                        matched_file = next((f for f in uploaded_files if f.name == filename), None)
                        if matched_file:
                            st.image(matched_file, caption=filename, use_container_width=True)

                    with c2:
                        st.markdown("### Rules Checklist")
                        for check_name, passed in checks.items():
                            label_str = check_name.replace("_", " ").title()
                            badge = "✅ Pass" if passed else "❌ Fail"
                            st.write(f"- **{label_str}**: {badge}")
                        
                        st.markdown("### Notes")
                        st.info(notes)
