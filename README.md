# DataSight: Secure Semantic Layer for Data & AI Modernization

DataSight is an intelligent, self-healing Text-to-SQL agent designed to democratize data access for non-technical enterprise business users. Built using **Anthropic's Claude 3.5 Sonnet** and orchestrated via **LangGraph**, it serves as a secure semantic abstraction layer over complex or legacy database architectures.

Business users can query relational databases using plain English, while an autonomous application-layer harness guarantees read-only security and handles real-time query repair.

## 🚀 Key Features & Hackathon Track Alignment

- **Spec-to-Data Pipeline:** Instantly compiles high-level human intent into context-optimized SQL queries, fetching structured data dynamically without manual developer dependency.
- **Data & AI Modernization:** Acts as a semantic shield over legacy schema structures. Organizations can migrate or refactor underlying physical databases without altering the business user's conversational interface.
- **Harness Engineering (Security Guardrails):** Programmatically intercepts LLM output at the application layer to strictly validate queries using regex boundary checking, blocking unauthorized DML/DDL commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
- **Self-Healing Execution Loop:** Implements an automated loop that catches database-level exceptions, pipes the diagnostic error payload back to Claude 3.5 Sonnet, and auto-corrects syntax bugs in milliseconds before final formatting.

---

## 🛠️ Tech Stack

- **Orchestration:** LangGraph
- **LLM Engine:** Anthropic Claude 3.5 Sonnet (`langchain-anthropic`)
- **Database Engine:** SQLite / SQLAlchemy (`langchain-community`)
- **Frontend Web UI:** Streamlit

---

## 📋 Installation & Local Setup

### 1. Clone the Repository

```bash
git clone [https://github.com/swapna-tw/globalhack_queryworks.git](https://github.com/swapna-tw/globalhack_queryworks.git)
cd globalhack_queryworks
```
