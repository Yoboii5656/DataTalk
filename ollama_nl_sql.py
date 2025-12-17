"""
Ollama Local LLM powered Natural Language to SQL Converter
Runs completely locally - no API costs, no internet needed, complete privacy
"""

import os
import requests
from typing import Tuple, Optional

class OllamaNLtoSQL:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama NL-to-SQL converter
        
        Args:
            model: Ollama model to use (e.g., 'llama3.1', 'mistral', 'codellama', 'deepseek-coder')
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Test connection
        if not self._test_connection():
            raise ConnectionError(
                f"Cannot connect to Ollama at {base_url}. "
                f"Make sure Ollama is running. Install from: https://ollama.ai"
            )
        
        self.schema_info = self._get_default_schema()
    
    def _test_connection(self) -> bool:
        """Test if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_default_schema(self) -> str:
        """Get default database schema information"""
        return """
DATABASE SCHEMA (SQLite):

-- Main entity tables
workspaces: id, name, owner_id, created_at, plan (free/pro/enterprise), status (active/suspended)
users: id, email, name, workspace_id, role (admin/member/viewer), created_at
agents: id, workspace_id, name, language (en/hi/gu/ta/te/mr/bn/kn/ml/pa), llm_model, status, created_at
integrations: id, workspace_id, type (hubspot/zoho/twilio/plivo/slack/custom), config, status, last_sync_at, created_at

-- Execution tables
agent_tools: id, agent_id, tool_name, tool_config, created_at
agent_runs: id, agent_id, workspace_id, run_type (live_call/test_call/cron_job/webhook), status (success/failed/partial), duration_ms, started_at, completed_at
test_runs: id, agent_id, workspace_id, test_input, expected_output, actual_output, result (pass/fail), error_message, created_at
run_logs: id, run_id, step, event_type (llm_call/tool_call/user_input/system), message, payload, timestamp

-- Error and sync tracking
errors: id, run_id, workspace_id, source (integration/agent/llm/tool), code, message, metadata, created_at
integration_sync_logs: id, integration_id, workspace_id, sync_type (contacts/deals/activities), status, items_synced, error_message, created_at

-- Analytics tables
billing_usage: id, workspace_id, agent_id, characters_generated, calls_made, tokens_used, total_cost_usd, created_at
audit_events: id, workspace_id, user_id, action (create/update/delete), entity, before, after, created_at

NOTES:
- This is SQLite, use: datetime('now'), datetime('now', '-7 days')
- Language codes: en=English, hi=Hindi, gu=Gujarati, ta=Tamil, etc.
- All IDs are TEXT (UUIDs stored as strings)
"""
    
    def parse_question(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert natural language question to SQL query using Ollama
        
        Args:
            question: Natural language question
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        try:
            prompt = f"""You are a SQL expert. Convert this natural language question into a SQLite query.

{self.schema_info}

RULES:
1. Return ONLY the SQL query, nothing else
2. Do NOT include explanations, markdown, or code blocks
3. Use proper SQLite syntax
4. Use appropriate JOINs when needed
5. For time queries use: datetime('now', '-N days/hours')
6. Query must be SELECT only (read-only)
7. Add ORDER BY and LIMIT when appropriate

QUESTION: {question}

SQL:"""

            # Call Ollama API
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent SQL
                        "top_p": 0.9,
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return None, f"Ollama API error: {response.status_code}"
            
            result = response.json()
            sql = result.get('response', '').strip()
            
            # Clean up the SQL
            sql = self._clean_sql(sql)
            
            if not sql:
                return None, "Could not generate SQL query. Please try rephrasing your question."
            
            # Validate it's a SELECT query
            if not sql.upper().startswith('SELECT'):
                return None, "Only SELECT queries are allowed for safety."
            
            explanation = f"Generated SQL using Ollama ({self.model})"
            return sql, explanation
            
        except requests.exceptions.Timeout:
            return None, "Ollama request timed out. The model might be slow or not loaded."
        except requests.exceptions.ConnectionError:
            return None, "Cannot connect to Ollama. Make sure Ollama is running."
        except Exception as e:
            return None, f"Error generating SQL: {str(e)}"
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up SQL query from LLM response"""
        # Remove markdown code blocks
        sql = sql.replace('```sql', '').replace('```', '')
        
        # Remove common prefixes
        prefixes = ['SQL:', 'Query:', 'Answer:', 'SELECT']
        for prefix in prefixes[:-1]:  # Don't remove SELECT
            if sql.startswith(prefix):
                sql = sql[len(prefix):].strip()
        
        # Take only the first query if multiple
        lines = sql.split('\n')
        sql_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            if line.upper().startswith('SELECT'):
                sql_lines = [line]
            elif sql_lines:
                sql_lines.append(line)
                if line.endswith(';'):
                    break
        
        sql = ' '.join(sql_lines) if sql_lines else sql.split('\n')[0]
        
        # Remove trailing semicolon
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
            "How many agents are there in total?",
            "Errors by source in the last month",
            "Agent runs by status",
            "Show me the top 10 workspaces by token usage",
            "List all successful test runs today",
            "Which agents have the longest average run duration?",
            "Show me all HubSpot integrations that failed to sync",
            "What are the most common error codes?",
            "Show billing usage for the last 30 days"
        ]
    
    def get_available_models(self) -> list:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception:
            return []
    
    def test_connection(self) -> bool:
        """Test if Ollama is working"""
        return self._test_connection()
