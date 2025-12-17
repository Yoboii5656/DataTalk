"""
Google Gemini AI powered Natural Language to SQL Converter
Uses Google's Gemini API for intelligent query generation
"""

import os
import google.generativeai as genai
from typing import Tuple, Optional

class GeminiNLtoSQL:
    def __init__(self, api_key: str = None, schema_info: str = None):
        """
        Initialize Gemini NL-to-SQL converter
        
        Args:
            api_key: Google API key (if None, reads from GOOGLE_API_KEY env var)
            schema_info: Database schema information
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.0 Flash Experimental (latest available model)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.schema_info = schema_info or self._get_default_schema()
    
    def _get_default_schema(self) -> str:
        """Get default database schema information"""
        return """
DATABASE SCHEMA:

Table: workspaces
- id (UUID PRIMARY KEY)
- name (TEXT)
- owner_id (UUID)
- created_at (TIMESTAMP)
- plan (TEXT: 'free', 'pro', 'enterprise')
- status (TEXT: 'active', 'suspended')

Table: users
- id (UUID PRIMARY KEY)
- email (TEXT)
- name (TEXT)
- workspace_id (UUID, references workspaces)
- role (TEXT: 'admin', 'member', 'viewer')
- created_at (TIMESTAMP)

Table: agents
- id (UUID PRIMARY KEY)
- workspace_id (UUID, references workspaces)
- name (TEXT)
- language (TEXT: 'en', 'hi', 'gu', 'ta', 'te', 'mr', 'bn', 'kn', 'ml', 'pa')
- llm_model (TEXT: 'gpt-4', 'gpt-3.5-turbo', etc.)
- status (TEXT: 'active', 'inactive')
- created_at (TIMESTAMP)

Table: integrations
- id (UUID PRIMARY KEY)
- workspace_id (UUID, references workspaces)
- type (TEXT: 'hubspot', 'zoho', 'twilio', 'plivo', 'slack', 'custom')
- config (JSONB)
- status (TEXT: 'active', 'inactive', 'error')
- last_sync_at (TIMESTAMP)
- created_at (TIMESTAMP)

Table: agent_tools
- id (UUID PRIMARY KEY)
- agent_id (UUID, references agents)
- tool_name (TEXT)
- tool_config (JSONB)
- created_at (TIMESTAMP)

Table: agent_runs
- id (UUID PRIMARY KEY)
- agent_id (UUID, references agents)
- workspace_id (UUID, references workspaces)
- run_type (TEXT: 'live_call', 'test_call', 'cron_job', 'webhook')
- status (TEXT: 'success', 'failed', 'partial')
- duration_ms (INTEGER)
- started_at (TIMESTAMP)
- completed_at (TIMESTAMP)

Table: test_runs
- id (UUID PRIMARY KEY)
- agent_id (UUID, references agents)
- workspace_id (UUID, references workspaces)
- test_input (TEXT)
- expected_output (TEXT)
- actual_output (TEXT)
- result (TEXT: 'pass', 'fail')
- error_message (TEXT)
- created_at (TIMESTAMP)

Table: run_logs
- id (UUID PRIMARY KEY)
- run_id (UUID, references agent_runs)
- step (INTEGER)
- event_type (TEXT: 'llm_call', 'tool_call', 'user_input', 'system')
- message (TEXT)
- payload (JSONB)
- timestamp (TIMESTAMP)

Table: errors
- id (UUID PRIMARY KEY)
- run_id (UUID, references agent_runs)
- workspace_id (UUID, references workspaces)
- source (TEXT: 'integration', 'agent', 'llm', 'tool')
- code (TEXT)
- message (TEXT)
- metadata (JSONB)
- created_at (TIMESTAMP)

Table: integration_sync_logs
- id (UUID PRIMARY KEY)
- integration_id (UUID, references integrations)
- workspace_id (UUID, references workspaces)
- sync_type (TEXT: 'contacts', 'deals', 'activities')
- status (TEXT: 'success', 'failed')
- items_synced (INTEGER)
- error_message (TEXT)
- created_at (TIMESTAMP)

Table: billing_usage
- id (UUID PRIMARY KEY)
- workspace_id (UUID, references workspaces)
- agent_id (UUID, references agents)
- characters_generated (INTEGER)
- calls_made (INTEGER)
- tokens_used (INTEGER)
- total_cost_usd (DECIMAL)
- created_at (TIMESTAMP)

Table: audit_events
- id (UUID PRIMARY KEY)
- workspace_id (UUID, references workspaces)
- user_id (UUID, references users)
- action (TEXT: 'create', 'update', 'delete')
- entity (TEXT)
- before (JSONB)
- after (JSONB)
- created_at (TIMESTAMP)

IMPORTANT NOTES:
- This is a SQLite database
- Use SQLite datetime functions: datetime('now'), datetime('now', '-7 days'), etc.
- Use date() for date extraction: date(created_at)
- Language codes: en=English, hi=Hindi, gu=Gujarati, ta=Tamil, te=Telugu, mr=Marathi, bn=Bengali, kn=Kannada, ml=Malayalam, pa=Punjabi
"""
    
    def parse_question(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert natural language question to SQL query using Gemini
        
        Args:
            question: Natural language question
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        try:
            prompt = f"""You are a SQL expert. Convert the following natural language question into a SQLite query.

{self.schema_info}

RULES:
1. Return ONLY the SQL query, nothing else
2. Do NOT include markdown formatting or code blocks
3. Use proper SQLite syntax
4. Use appropriate JOINs when needed
5. Add ORDER BY and LIMIT when appropriate
6. For time-based queries, use SQLite datetime functions
7. Make sure the query is safe and read-only (SELECT only)

QUESTION: {question}

SQL QUERY:"""

            # Generate SQL using Gemini
            response = self.model.generate_content(prompt)
            sql = response.text.strip()
            
            # Clean up the response
            sql = self._clean_sql(sql)
            
            if not sql:
                return None, "Could not generate SQL query. Please try rephrasing your question."
            
            # Validate it's a SELECT query
            if not sql.upper().startswith('SELECT'):
                return None, "Only SELECT queries are allowed for safety."
            
            explanation = f"Generated SQL query for: {question}"
            return sql, explanation
            
        except Exception as e:
            return None, f"Error generating SQL: {str(e)}"
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up SQL query from Gemini response"""
        # Remove markdown code blocks if present
        sql = sql.replace('```sql', '').replace('```', '')
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Remove any explanatory text before or after the query
        lines = sql.split('\n')
        sql_lines = []
        in_query = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('SELECT'):
                in_query = True
            if in_query:
                sql_lines.append(line)
                if line.endswith(';'):
                    break
        
        sql = ' '.join(sql_lines)
        
        # Remove trailing semicolon if present
        sql = sql.rstrip(';').strip()
        
        return sql
    
    def get_suggestions(self) -> list:
        """Get list of example questions"""
        return [
            "Top 5 errors for the last 24 hours",
            "Show all failed test runs from last week",
            "Which integrations are inactive",
            "List all agents using Gujarati language",
            "Show all workspaces with more than 5 agents",
            "What are the most expensive workspaces by billing?",
            "How many agents",
            "Errors by source in the last month",
            "Agent runs by status",
            "Show me the top 10 workspaces by token usage",
            "List all successful test runs today",
            "Which agents have the longest average run duration?",
            "Show me all HubSpot integrations that failed to sync",
            "What are the most common error codes?",
            "Show billing usage for the last 30 days"
        ]
    
    def test_connection(self) -> bool:
        """Test if Gemini API is working"""
        try:
            response = self.model.generate_content("Say 'OK' if you can read this.")
            return 'ok' in response.text.lower()
        except Exception:
            return False
