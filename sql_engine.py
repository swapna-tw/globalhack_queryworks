# sql_engine.py
import sqlite3
import re
from typing import TypedDict, Optional

# LangChain & LangGraph Imports
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

class NativeDBHelper:
    """A metadata-isolated database tool mapping schemas without revealing row data."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.dialect = "sqlite"

    def get_table_info(self) -> str:
        """Acts as our abstract data dictionary for the prompt window context."""
        schema_info = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                schema_info.append(f"Table: {table}")
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                cols_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
                schema_info.append(f"Columns: {cols_str}\n")
        return "\n".join(schema_info)

    def run(self, query: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            return str(results)


class State(TypedDict):
    question: str
    generated_sql: Optional[str]
    sql_result: Optional[str]
    final_answer: Optional[str]
    error: Optional[str]


class SafeSQLGraphEngine:
    def __init__(self, db_path: str):
        self.db = NativeDBHelper(db_path)
        
        self.llm = init_chat_model("claude-sonnet-4-6", model_provider="anthropic", temperature=0)
        self.app = self._build_graph()

    def generate_query_node(self, state: State) -> dict:
        schema = self.db.get_table_info()
        dialect = self.db.dialect
        
        # Text-to-SQL optimization template
        base_prompt = """You are a database master. Given a business user question and a database schema, write a syntactically correct {dialect} query that will fetch the required data.
            
            CRITICAL RULES:
            - You must ONLY return read-only SELECT statements.
            - Do NOT try to modify, add, or delete data.
            - Return ONLY the executable SQL query string. Do NOT wrap it in markdown code blocks like ```sql.

            Database Schema Map (Data Dictionary):
            {schema}"""

        if state.get("error") and state.get("generated_sql"):
            base_prompt += f"\n\nCRITICAL FIX REQUIRED: Your previous attempt failed with error: {state['error']}\nPlease correct the syntax for this original query: {state['generated_sql']}"

        base_prompt += "\n\nUser Question: {question}\nSQL Query:"        
        
        prompt_template = PromptTemplate.from_template(base_prompt)
        prompt = prompt_template.format(dialect=dialect, schema=schema, question=state["question"])
        response = self.llm.invoke(prompt)
        return {"generated_sql": response.content.strip(), "error": None}

    def execute_query_node(self, state: State) -> dict:
        query = state["generated_sql"]
        clean_query = query.strip().replace("```sql", "").replace("```", "").strip()
        forbidden_keywords = [r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b", r"\bREPLACE\b", r"\bTRUNCATE\b"]
        
        for pattern in forbidden_keywords:
            if re.search(pattern, clean_query, re.IGNORECASE):
                return {"error": "Security Block: Query contained prohibited DML/DDL modifications."}
        
        try:
            result = self.db.run(clean_query)
            return {"sql_result": str(result), "error": None}
        except Exception as e:
            return {"error": f"Database execution error: {str(e)}", "retry_count": state.get("retry_count", 0) + 1}

    def format_answer_node(self, state: State) -> dict:
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

    def evaluate_execution_state(self, state: State):
        """Orchestrates Self-Healing Loop and Security Exception routing."""
        if state.get("error"):
            if "Security Block" in state["error"]:
                return "format_answer"  # Jump straight to end-block display
            if state.get("retry_count", 0) <= 2:
                return "generate_query" # Activate the Self-Healing feedback loop
            return "format_answer"
        return "format_answer"

    def _build_graph(self):
        workflow = StateGraph(State)
        
        workflow.add_node("generate_query", self.generate_query_node)
        workflow.add_node("execute_query", self.execute_query_node)
        workflow.add_node("format_answer", self.format_answer_node)
        
        workflow.add_edge(START, "generate_query")
        workflow.add_edge("generate_query", "execute_query")
        
        workflow.add_conditional_edges(
            "execute_query",
            self.evaluate_execution_state,
            {
                "generate_query": "generate_query",
                "format_answer": "format_answer"
            }
        )
        
        workflow.add_edge("format_answer", END)
        return workflow.compile()

    def ask(self, query_string: str) -> str:
        initial_state = {
            "question": query_string,
            "generated_sql": None,
            "sql_result": None,
            "final_answer": None,
            "error": None,
            "retry_count": 0
        }
        output = self.app.invoke(initial_state)
        return output["final_answer"]