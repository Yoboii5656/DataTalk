"""
Vanna AI powered Natural Language to SQL Converter
Industry-standard solution specifically designed for NL-to-SQL
"""

import os
from typing import Tuple, Optional
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

class VannaNLtoSQL(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, api_key: str = None, schema_info: str = None):
        """
        Initialize Vanna AI with OpenAI backend
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            schema_info: Database schema information
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required for Vanna AI. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize ChromaDB for vector storage (local, no external service needed)
        ChromaDB_VectorStore.__init__(self, config={'path': './vanna_chromadb'})
        
        # Initialize OpenAI Chat
        OpenAI_Chat.__init__(self, config={'api_key': self.api_key, 'model': 'gpt-4o-mini'})
        
        # Train on schema if provided
        if schema_info:
            self._train_on_schema(schema_info)
        else:
            self._train_on_default_schema()
    
    def _train_on_default_schema(self):
        """Train Vanna on the default database schema"""
        # DDL Statements
        ddl = """
        CREATE TABLE workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id TEXT,
            created_at TIMESTAMP,
            plan TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active'
        );
        
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            workspace_id TEXT REFERENCES workspaces(id),
            role TEXT DEFAULT 'member',
            created_at TIMESTAMP
        );
        
        CREATE TABLE agents (
            id TEXT PRIMARY KEY,
            workspace_id TEXT REFERENCES workspaces(id),
            name TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            llm_model TEXT DEFAULT 'gpt-4',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP
        );
        
        CREATE TABLE integrations (
            id TEXT PRIMARY KEY,
            workspace_id TEXT REFERENCES workspaces(id),
            type TEXT NOT NULL,
            config TEXT,
            status TEXT DEFAULT 'active',
            last_sync_at TIMESTAMP,
            created_at TIMESTAMP
        );
        
        CREATE TABLE agent_tools (
            id TEXT PRIMARY KEY,
            agent_id TEXT REFERENCES agents(id),
            tool_name TEXT NOT NULL,
            tool_config TEXT,
            created_at TIMESTAMP
        );
        
        CREATE TABLE agent_runs (
            id TEXT PRIMARY KEY,
            agent_id TEXT REFERENCES agents(id),
            workspace_id TEXT REFERENCES workspaces(id),
            run_type TEXT DEFAULT 'test_call',
            status TEXT DEFAULT 'success',
            duration_ms INTEGER,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        CREATE TABLE test_runs (
            id TEXT PRIMARY KEY,
            agent_id TEXT REFERENCES agents(id),
            workspace_id TEXT REFERENCES workspaces(id),
            test_input TEXT,
            expected_output TEXT,
            actual_output TEXT,
            result TEXT DEFAULT 'pass',
            error_message TEXT,
            created_at TIMESTAMP
        );
        
        CREATE TABLE run_logs (
            id TEXT PRIMARY KEY,
            run_id TEXT REFERENCES agent_runs(id),
            step INTEGER,
            event_type TEXT,
            message TEXT,
            payload TEXT,
            timestamp TIMESTAMP
        );
        
        CREATE TABLE errors (
            id TEXT PRIMARY KEY,
            run_id TEXT REFERENCES agent_runs(id),
            workspace_id TEXT REFERENCES workspaces(id),
            source TEXT,
            code TEXT,
            message TEXT,
            metadata TEXT,
            created_at TIMESTAMP
        );
        
        CREATE TABLE integration_sync_logs (
            id TEXT PRIMARY KEY,
            integration_id TEXT REFERENCES integrations(id),
            workspace_id TEXT REFERENCES workspaces(id),
            sync_type TEXT,
            status TEXT DEFAULT 'success',
            items_synced INTEGER,
            error_message TEXT,
            created_at TIMESTAMP
        );
        
        CREATE TABLE billing_usage (
            id TEXT PRIMARY KEY,
            workspace_id TEXT REFERENCES workspaces(id),
            agent_id TEXT REFERENCES agents(id),
            characters_generated INTEGER,
            calls_made INTEGER,
            tokens_used INTEGER,
            total_cost_usd REAL,
            created_at TIMESTAMP
        );
        
        CREATE TABLE audit_events (
            id TEXT PRIMARY KEY,
            workspace_id TEXT REFERENCES workspaces(id),
            user_id TEXT REFERENCES users(id),
            action TEXT,
            entity TEXT,
            before TEXT,
            after TEXT,
            created_at TIMESTAMP
        );
        """
        
        # Documentation
        documentation = """
        This database stores data for a multi-tenant voice agent platform.
        
        Tables and their purposes:
        - workspaces: Customer accounts/organizations. Each workspace has a plan (free/pro/enterprise) and status (active/suspended).
        - users: Users belonging to workspaces with roles (admin/member/viewer).
        - agents: Voice agents configured in each workspace. Each agent has a language code (en=English, hi=Hindi, gu=Gujarati, ta=Tamil, etc.) and an LLM model.
        - integrations: External integrations like HubSpot, Zoho, Twilio, Plivo, Slack, or custom APIs. Status can be active, inactive, or error.
        - agent_tools: Tools attached to agents like CRM Lookup, Email Sender, HubSpot API, etc.
        - agent_runs: Records of agent executions. run_type can be live_call, test_call, cron_job, or webhook. status is success, failed, or partial.
        - test_runs: Test executions with result being pass or fail.
        - run_logs: Detailed logs during agent runs with event_type being llm_call, tool_call, user_input, or system.
        - errors: System-level and run-level failures with source being integration, agent, llm, or tool.
        - integration_sync_logs: Sync activity logs for integrations like HubSpot/Zoho data fetching. sync_type is contacts, deals, or activities.
        - billing_usage: Usage metrics per agent including characters, calls, tokens, and cost.
        - audit_events: Change tracking for who did what, with action being create, update, or delete.
        
        Language codes used: en (English), hi (Hindi), gu (Gujarati), ta (Tamil), te (Telugu), mr (Marathi), bn (Bengali), kn (Kannada), ml (Malayalam), pa (Punjabi).
        
        This is a SQLite database. Use SQLite datetime functions like datetime('now'), datetime('now', '-7 days'), etc.
        """
        
        # Sample questions and SQL
        samples = [
            ("Top 5 errors for the last 24 hours", 
             "SELECT code, message, source, COUNT(*) as error_count FROM errors WHERE created_at >= datetime('now', '-24 hours') GROUP BY code, message, source ORDER BY error_count DESC LIMIT 5"),
            
            ("Show all failed test runs from last week",
             "SELECT tr.*, a.name as agent_name FROM test_runs tr JOIN agents a ON tr.agent_id = a.id WHERE tr.result = 'fail' AND tr.created_at >= datetime('now', '-7 days') ORDER BY tr.created_at DESC"),
            
            ("Which integrations are inactive",
             "SELECT i.*, w.name as workspace_name FROM integrations i JOIN workspaces w ON i.workspace_id = w.id WHERE i.status = 'inactive'"),
            
            ("List all agents using Gujarati language",
             "SELECT a.*, w.name as workspace_name FROM agents a JOIN workspaces w ON a.workspace_id = w.id WHERE a.language = 'gu'"),
        ]
        
        # Train Vanna
        try:
            self.train(ddl=ddl)
            self.train(documentation=documentation)
            for question, sql in samples:
                self.train(question=question, sql=sql)
        except Exception as e:
            print(f"Warning: Training failed: {e}")
    
    def _train_on_schema(self, schema_info: str):
        """Train Vanna on custom schema"""
        try:
            self.train(ddl=schema_info)
        except Exception as e:
            print(f"Warning: Training failed: {e}")
    
    def parse_question(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert natural language question to SQL query using Vanna AI
        
        Args:
            question: Natural language question
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        try:
            # Generate SQL using Vanna
            sql = self.generate_sql(question)
            
            if not sql:
                return None, "Could not generate SQL query. Please try rephrasing your question."
            
            # Clean up the SQL
            sql = sql.strip()
            if sql.endswith(';'):
                sql = sql[:-1]
            
            # Validate it's a SELECT query
            if not sql.upper().startswith('SELECT'):
                return None, "Only SELECT queries are allowed for safety."
            
            explanation = f"Generated SQL query using Vanna AI for: {question}"
            return sql, explanation
            
        except Exception as e:
            return None, f"Error generating SQL: {str(e)}"
    
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
    
    def test_connection(self) -> bool:
        """Test if Vanna AI is working"""
        try:
            sql = self.generate_sql("SELECT 1")
            return sql is not None
        except Exception:
            return False
