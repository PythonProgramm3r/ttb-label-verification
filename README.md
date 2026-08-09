readme_content = """# TTB Label Verification System

An automated, AI-powered compliance verification portal designed to evaluate alcohol beverage labels against mandatory Alcohol and Tobacco Tax and Trade Bureau (TTB) regulatory standards. Built with Python, Streamlit, and Azure OpenAI Service, this application processes batch label uploads concurrently and returns detailed audit findings in real time.

---

## Key Features

* **Multimodal Visual Inspection:** Utilizes Azure OpenAI vision models (`gpt-4.1-mini`) to read, extract, and analyze text directly from alcohol label images.
* **Asynchronous Batch Processing:** Employs Python’s `asyncio` framework with semaphore controls to process multiple label images concurrently.
* **Structured Compliance Checklist:** Evaluates labels against five core TTB regulatory checks and outputs structured pass/fail decisions alongside explanatory audit notes.
* **Secure Enterprise Architecture:** Uses server-side secrets management (`st.secrets`) to keep Azure API keys, endpoints, and deployment details completely decoupled from client code and source control.
* **Optimized Batch Workflow:** Features custom interface enhancements to streamline batch evaluation via direct drag-and-drop interactions.

---

## Technical Architecture

* **Frontend Framework:** Streamlit
* **Cloud & AI Infrastructure:** Azure OpenAI Service (Microsoft Azure AI Foundry)
* **Core Language & Libraries:** Python 3.11+, `openai` (AsyncAzureOpenAI), `asyncio`, `base64`, `json`
* **Version Control & Hosting:** GitHub, Streamlit Community Cloud

---

## Evaluated Compliance Rules

The verification engine checks each uploaded label against five core TTB requirements:

| Compliance Item | Requirement Description |
| :--- | :--- |
| **Brand Name** | Must be clearly stated and legible on the label. |
| **Class / Type** | Must explicitly state the product classification (e.g., *Vodka*, *Bourbon*, *Wine*). |
| **Alcohol Content (ABV)** | Must display the Alcohol by Volume percentage. |
| **Net Contents** | Must state the net volume (e.g., *750 mL*, *12 fl. oz.*). |
| **Government Warning** | Must contain the exact, mandatory federal health warning statement. |

---

## Repository Structure

```text
.
├── app.py              # Main Streamlit application and async processing pipeline
├── requirements.txt    # Python dependencies (streamlit, openai)
└── README.md           # System documentation
