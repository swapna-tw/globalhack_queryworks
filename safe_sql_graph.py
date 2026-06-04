import os
import sqlite3
import re
from typing import TypedDict, Optional

# LangChain / Anthropic Imports
from langchain_community.utilities import SQLDatabase
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate

# LangGraph Imports
from langgraph.graph import StateGraph, START, END

# ==========================================
# STEP 1: SETUP SAMPLE DATABASE
# ==========================================
def setup_sample_database():
    db_name = "organization_vault.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS external_entities (
        entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        entity_type TEXT CHECK(entity_type IN ('Vendor', 'Client', 'Partner')),
        contact_email TEXT,
        country TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        transaction_date DATE DEFAULT CURRENT_DATE,
        amount REAL NOT NULL,
        status TEXT CHECK(status IN ('Pending', 'Completed', 'Failed')),
        description TEXT,
        FOREIGN KEY (entity_id) REFERENCES external_entities(entity_id)
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM external_entities;")
    if cursor.fetchone()[0] == 0:
        entities = [
            ('Apex Logistics', 'Vendor', 'billing@apex.com', 'USA'),
            ('Global Tech Corp', 'Client', 'accounts@globaltech.io', 'Canada'),
            ('Acme Manufacturing', 'Vendor', 'supply@acme.com', 'Germany'),
            ('Delta Consulting', 'Partner', 'info@deltaconsult.com', 'UK')
        ]
        cursor.executemany("INSERT INTO external_entities (company_name, entity_type, contact_email, country) VALUES (?, ?, ?, ?);", entities)

        transactions = [
            (1, '2026-01-15', 15000.00, 'Completed', 'Monthly fleet shipping fees'),
            (2, '2026-02-10', 45000.50, 'Completed', 'Q1 Software licensing renewal'),
            (3, '2026-03-01', 8200.00, 'Pending', 'Raw materials batch #42'),
            (1, '2026-03-12', 3200.00, 'Failed', 'Urgent courier delivery'),
            (4, '2026-04-18', 12500.00, 'Completed', 'Joint venture marketing consultation')
        ]
        cursor.executemany("INSERT INTO transactions (entity_id, transaction_date, amount, status, description) VALUES (?, ?, ?, ?, ?);", transactions)

    conn.commit()
    conn.close()
    return db_name


# ==========================================
# STEP 2: DEFINE LANGGRAPH STATE & ENGINE
# ==========================================

# Define the data structure that passes between graph nodes
class State(TypedDict):
    question: str
    generated_sql: Optional[str]
    sql_result: Optional[str]
    final_answer: Optional[str]
    error: Optional[str]


class SafeSQLGraphEngine:
    def __init__(self, db_path: str):
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        # Using Claude 4.6 Sonnet
        self.llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
        
        # Build our orchestrated workflow graph
        self.app = self._build_graph()

    # --- NODE 1: Generate SQL Query ---
    def generate_query_node(self, state: State) -> dict:
        schema = self.db.get_table_info()
        dialect = self.db.dialect
        
        prompt_template = PromptTemplate.from_template(
            """You are a database master. Given a business user question and a database schema, write a syntactically correct {dialect} query that will fetch the required data.
            
            CRITICAL RULES:
            - You must ONLY return read-only SELECT statements.
            - Do NOT try to modify, add, or delete data.
            - Return ONLY the executable SQL query string. Do NOT wrap it in markdown code blocks like ```sql.

            Database Schema:
            {schema}

            User Question: {question}
            SQL Query:"""
        )
        
        prompt = prompt_template.format(dialect=dialect, schema=schema, question=state["question"])
        response = self.llm.invoke(prompt)
        
        return {"generated_sql": response.content.strip()}

    # --- NODE 2: Guardrail & Execute Query ---
    def execute_query_node(self, state: State) -> dict:
        query = state["generated_sql"]
        
        # Security sanitization check
        clean_query = query.strip().replace("```sql", "").replace("```", "").strip()
        forbidden_keywords = [r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b", r"\bREPLACE\b", r"\bTRUNCATE\b"]
        
        for pattern in forbidden_keywords:
            if re.search(pattern, clean_query, re.IGNORECASE):
                return {"error": "Security Block: Query contained prohibited DML/DDL modifications."}
        
        # If passed guardrails, physically query the DB
        try:
            result = self.db.run(clean_query)
            return {"sql_result": str(result)}
        except Exception as e:
            return {"error": f"Database execution error: {str(e)}"}

    # --- NODE 3: Format Human-Friendly Output ---
    def format_answer_node(self, state: State) -> dict:
        # If an error occurred earlier in the graph, don't generate a normal answer
        if state.get("error"):
            return {"final_answer": f"❌ Action Blocked: {state['error']}"}
            
        prompt_template = PromptTemplate.from_template(
            """You are a professional business translator. Review the original user question, the generated SQL query used, and the raw data result fetched from our database. Format this into a clear, helpful corporate response.
            
            User Question: {question}
            SQL Query Used: {query}
            Database Result: {result}
            
            Business Answer:"""
        )
        
        prompt = prompt_template.format(
            question=state["question"],
            query=state["generated_sql"],
            result=state["sql_result"]
        )
        
        response = self.llm.invoke(prompt)
        return {"final_answer": response.content.strip()}

    # --- ROUTING LOGIC ---
    def check_for_errors(self, state: State):
        """Conditional routing logic determining if we should proceed or short-circuit."""
        if state.get("error") is not None:
            return "format_answer"  # Jump straight to displaying the error safely
        return "format_answer"

    # --- ORCHESTRATE GRAPH ---
    def _build_graph(self):
        workflow = StateGraph(State)
        
        # Define the processing nodes
        workflow.add_node("generate_query", self.generate_query_node)
        workflow.add_node("execute_query", self.execute_query_node)
        workflow.add_node("format_answer", self.format_answer_node)
        
        # Build structural edges
        workflow.add_edge(START, "generate_query")
        workflow.add_edge("generate_query", "execute_query")
        
        # Conditional edge: If Node 2 hits a security trigger, route appropriately
        workflow.add_conditional_edges(
            "execute_query",
            self.check_for_errors,
            {
                "format_answer": "format_answer"
            }
        )
        
        workflow.add_edge("format_answer", END)
        return workflow.compile()

    def ask(self, query_string: str):
        # Run the compiled state graph
        initial_state = {
            "question": query_string,
            "generated_sql": None,
            "sql_result": None,
            "final_answer": None,
            "error": None
        }
        output = self.app.invoke(initial_state)
        return output["final_answer"]


# ==========================================
# STEP 3: RUN AND TEST APPLICATION
# ==========================================
if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Please set your ANTHROPIC_API_KEY environment variable.")
        exit(1)

    db_file = setup_sample_database()
    engine = SafeSQLGraphEngine(db_file)

    # Test 1: Clean, regular business query
    q1 = "Show me all details about our transactions with Global Tech Corp."
    print(f"💼 Business User: '{q1}'")
    print(f"🤖 Claude App:\n{engine.ask(q1)}\n")
    print("-" * 60)

    # Test 2: Adversarial user trying to force a DML/modification query
    q2 = "Update our transactions and change the amount to 0 for entity_id 1."
    print(f"💼 Business User: '{q2}'")
    print(f"🤖 Claude App:\n{engine.ask(q2)}\n")
    print("-" * 60)
