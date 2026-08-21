# Developer: Devvrat Welekar
import os
import re

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
        if not user_question or len(user_question) > 1000:
            return "", "Query must contain between 1 and 1,000 characters."

        raw_response = self.chain.invoke({"schema": self.schema, "question": user_question})
        clean_sql = raw_response.strip().replace("```sql", "").replace("```", "").replace("`", "")

        validation_error = self._validate_read_only_sql(clean_sql)
        if validation_error:
            return clean_sql, validation_error
        
        try:
            result_df = self.conn.execute(clean_sql).fetchdf()
            return clean_sql, result_df
        except Exception as e:
            return clean_sql, f"Execution Error: {str(e)}"

    @staticmethod
    def _validate_read_only_sql(sql):
        normalized_sql = re.sub(r"\s+", " ", sql.strip()).upper()
        if not normalized_sql:
            return "SQL validation error: the model returned an empty query."
        if ";" in normalized_sql.rstrip(";"):
            return "SQL validation error: multiple SQL statements are not allowed."
        if not normalized_sql.startswith("SELECT ") and normalized_sql != "SELECT":
            return "SQL validation error: only SELECT queries are allowed."
        if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|COPY|EXPORT|ATTACH|DETACH|CALL|INSTALL|LOAD)\b", normalized_sql):
            return "SQL validation error: write and administrative statements are not allowed."
        return None