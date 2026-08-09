# TTB Label Verification System

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
```

---

## Setup & Local Development

### 1. Prerequisites
* Python 3.10+ installed locally
* An active Azure OpenAI resource with a deployed vision-capable model (e.g., `gpt-4.1-mini` or `gpt-4o`)

### 2. Installation
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/PythonProgramm3r/ttb-label-verification.git
cd ttb-label-verification
pip install -r requirements.txt
```

### 3. Environment Secrets Configuration
Create a local `.streamlit/secrets.toml` file to store your Azure credentials securely:

```toml
AZURE_API_KEY = "your-azure-api-key"
AZURE_ENDPOINT = "https://your-resource-name.openai.azure.com/"
AZURE_DEPLOYMENT = "gpt-4.1-mini"
```

### 4. Running the Application
Launch the Streamlit portal locally:

```bash
streamlit run app.py
```

---

## Security & Usage Notes

* **Official Use Banner:** Configured with strict internal portal messaging for presentation environments.
* **Zero Credential Exposure:** Secrets are managed via Streamlit Community Cloud Secrets in production and local `secrets.toml` during development, ensuring no API keys or endpoints are committed to GitHub.
