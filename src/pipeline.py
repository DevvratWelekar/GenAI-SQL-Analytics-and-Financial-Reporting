# Developer: Devvrat Welekar
import os

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

class TextToSQLPipeline:
    def __init__(self, conn, schema_str, model_name=None):
        self.conn = conn
        self.schema = schema_str
        self.llm = Ollama(
            model=model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            temperature=0,
        )
        
        template = """
        You are an expert Data Science assistant specializing in DuckDB SQL analytics.
        Given the table named 'sales' with the following layout schema:
        Columns: {schema}

        Convert the user's plain English request into a single, valid SQL query.
        Return ONLY the raw SQL code. Do not include markdown backticks, explanations, or quotes.

        User Request: {question}
        SQL Query:"""
        
        self.prompt = PromptTemplate(template=template, input_variables=["schema", "question"])
        self.chain = self.prompt | self.llm

    def execute_query(self, user_question):
        raw_response = self.chain.invoke({"schema": self.schema, "question": user_question})
        clean_sql = raw_response.strip().replace("```sql", "").replace("```", "").replace("`", "")
        
        try:
            result_df = self.conn.execute(clean_sql).fetchdf()
            return clean_sql, result_df
        except Exception as e:
            return clean_sql, f"Execution Error: {str(e)}"