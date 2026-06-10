# DataSight: Secure Semantic Layer for Data & AI Modernization

DataSight is an intelligent, self-healing Text-to-SQL agent designed to democratize data access for non-technical enterprise business users. Built using **Anthropic's Claude 4.6 Sonnet** and orchestrated via **LangGraph**, it serves as a secure semantic abstraction layer over complex or legacy database architectures.

Business users can query relational databases using plain English, while an autonomous application-layer harness guarantees read-only security and handles real-time query repair.

## 🚀 Key Features & Hackathon Track Alignment

- **Spec-to-Data Pipeline:** Instantly compiles high-level human intent into context-optimized SQL queries, fetching structured data dynamically without manual developer dependency.
- **Data & AI Modernization:** Acts as a semantic shield over legacy schema structures. Organizations can migrate or refactor underlying physical databases without altering the business user's conversational interface.
- **Harness Engineering (Security Guardrails):** Programmatically intercepts LLM output at the application layer to strictly validate queries using regex boundary checking, blocking unauthorized DML/DDL commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
- **Self-Healing Execution Loop:** Implements an automated loop that catches database-level exceptions, pipes the diagnostic error payload back to Claude 3.5 Sonnet, and auto-corrects syntax bugs in milliseconds before final formatting.

---

## 🛠️ Tech Stack

- **Orchestration & State Management:** LangGraph
- **Cognitive Core (LLM Engine):** Anthropic Claude 4.6 Sonnet via the unified initializer (init_chat_model)
- **Prompt Templating:** Core Prompt Utilities (PromptTemplate)
- **Database Engine:** Native Python 3 (sqlite3 local connection driver)
- **Frontend Web UI:** Streamlit

---

## 📋 Installation & Local Setup

### 1. Clone the Repository

git clone [https://github.com/swapna-tw/globalhack_queryworks.git](https://github.com/swapna-tw/globalhack_queryworks.git)
cd globalhack_queryworks

### 2. Configure Your Virtual Environment

Isolate your workspace packages from your global system environment.
**python3 -m venv .venv && source .venv/bin/activate**

### 3. Install Required Dependencies

Install the updated, modularized LangChain packages along with LangGraph and Streamlit:
**pip install -U langchain langchain-core langchain-anthropic langgraph streamlit**

### 4. Authenticate the AI Engine (Set API Key)

Set your Anthropic credentials as an environment variable so the semantic layer can securely query Claude 4.6 Sonnet.
**export ANTHROPIC_API_KEY="your-actual-api-key-here"**

## 🧪 Running the Execution Vectors

### Vector A: Automated Terminal Diagnostics (main.py)

To test the core graph engine, self-healing matrix, and security exceptions right in your console, run the automated integration test script. This script automatically instantiates the relational database file, seeds it with mock operational data, and tests both normal business questions and adversarial prompt injections:
**python main.py**

### Vector B: Interactive Web Dashboard (app.py)

To launch the complete, conversational graphical user interface for business stakeholders, run the Streamlit app. This opens an interactive application playground in your local web browser:
**streamlit run app.py**
