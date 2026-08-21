# Developer: Devvrat Welekar
import os
import re

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

class TextToSQLPipeline:
    MAX_REPAIR_ATTEMPTS = 2

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

        repair_template = """
        You are a SQL repair agent for DuckDB.
        Given the sales table schema, the user's request, the previous SQL, and the database error,
        return one corrected, read-only SQL query only. Do not use markdown or explanations.

        Schema: {schema}
        User Request: {question}
        Previous SQL: {sql}
        Database Error: {error}
        Corrected SQL:
        """
        self.repair_prompt = PromptTemplate(
            template=repair_template,
            input_variables=["schema", "question", "sql", "error"],
        )
        self.repair_chain = self.repair_prompt | self.llm

    def execute_query(self, user_question):
        if not user_question or len(user_question) > 1000:
            return "", "Query must contain between 1 and 1,000 characters."

        try:
            raw_response = self.chain.invoke({"schema": self.schema, "question": user_question})
        except Exception as error:
            return "", f"LLM error: {error}"

        clean_sql = self._clean_sql(raw_response)
        last_error = None
        for attempt in range(self.MAX_REPAIR_ATTEMPTS + 1):
            validation_error = self._validate_read_only_sql(clean_sql)
            if validation_error:
                last_error = validation_error
            else:
                try:
                    result_df = self.conn.execute(clean_sql).fetchdf()
                    return clean_sql, result_df
                except Exception as error:
                    last_error = f"Execution Error: {error}"

            if attempt == self.MAX_REPAIR_ATTEMPTS:
                break
            try:
                repaired_response = self.repair_chain.invoke(
                    {
                        "schema": self.schema,
                        "question": user_question,
                        "sql": clean_sql,
                        "error": last_error,
                    }
                )
            except Exception as error:
                return clean_sql, f"SQL repair error after attempt {attempt + 1}: {error}"
            clean_sql = self._clean_sql(repaired_response)

        return clean_sql, f"Query failed after {self.MAX_REPAIR_ATTEMPTS} repair attempts: {last_error}"

    @staticmethod
    def _clean_sql(raw_response):
        return raw_response.strip().replace("```sql", "").replace("```", "").replace("`", "")

    @staticmethod
    def _validate_read_only_sql(sql):
        normalized_sql = re.sub(r"\s+", " ", sql.strip()).upper()
        if not normalized_sql:
            return "SQL validation error: the model returned an empty query."
        if ";" in normalized_sql.rstrip(";"):
            return "SQL validation error: multiple SQL statements are not allowed."
        if not (
            normalized_sql.startswith("SELECT ")
            or normalized_sql == "SELECT"
            or normalized_sql.startswith("WITH ")
        ):
            return "SQL validation error: only SELECT queries are allowed."
        if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|COPY|EXPORT|ATTACH|DETACH|CALL|INSTALL|LOAD)\b", normalized_sql):
            return "SQL validation error: write and administrative statements are not allowed."
        return None