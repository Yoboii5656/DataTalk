"""
Local Natural Language to SQL Converter
No external APIs required - works completely offline
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class LocalNLtoSQL:
    def __init__(self):
        self.tables = {
            'workspaces': ['id', 'name', 'owner_id', 'created_at', 'plan', 'status'],
            'users': ['id', 'email', 'name', 'workspace_id', 'role', 'created_at'],
            'agents': ['id', 'workspace_id', 'name', 'language', 'llm_model', 'status', 'created_at'],
            'integrations': ['id', 'workspace_id', 'type', 'config', 'status', 'last_sync_at', 'created_at'],
            'agent_tools': ['id', 'agent_id', 'tool_name', 'tool_config', 'created_at'],
            'agent_runs': ['id', 'agent_id', 'workspace_id', 'run_type', 'status', 'duration_ms', 'started_at', 'completed_at'],
            'test_runs': ['id', 'agent_id', 'workspace_id', 'test_input', 'expected_output', 'actual_output', 'result', 'error_message', 'created_at'],
            'run_logs': ['id', 'run_id', 'step', 'event_type', 'message', 'payload', 'timestamp'],
            'errors': ['id', 'run_id', 'workspace_id', 'source', 'code', 'message', 'metadata', 'created_at'],
            'integration_sync_logs': ['id', 'integration_id', 'workspace_id', 'sync_type', 'status', 'items_synced', 'error_message', 'created_at'],
            'billing_usage': ['id', 'workspace_id', 'agent_id', 'characters_generated', 'calls_made', 'tokens_used', 'total_cost_usd', 'created_at'],
            'audit_events': ['id', 'workspace_id', 'user_id', 'action', 'entity', 'before', 'after', 'created_at']
        }
        
        self.languages = {
            'english': 'en', 'hindi': 'hi', 'gujarati': 'gu', 'tamil': 'ta',
            'telugu': 'te', 'marathi': 'mr', 'bengali': 'bn', 'kannada': 'kn',
            'malayalam': 'ml', 'punjabi': 'pa'
        }
        
        # Common query patterns
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> List[Dict]:
        """Build regex patterns for common query types"""
        return [
            # Top/Most queries
            {
                'pattern': r'top\s+(\d+)\s+errors?\s+(?:for|in|from)?\s*(?:the)?\s*last\s+(\d+)\s+(hour|day|week|month)s?',
                'handler': self._handle_top_errors
            },
            {
                'pattern': r'(?:show|list|get|find)\s+(?:all\s+)?errors?\s+(?:for|in|from)?\s*(?:the)?\s*last\s+(\d+)\s+(hour|day|week|month)s?',
                'handler': self._handle_errors_timeframe
            },
            
            # Failed/Success queries
            {
                'pattern': r'(?:show|list|get|find)\s+(?:all\s+)?failed\s+test\s*runs?\s+(?:for|in|from)?\s*(?:the)?\s*last\s+(\d+)\s+(hour|day|week|month)s?',
                'handler': self._handle_failed_tests
            },
            {
                'pattern': r'(?:show|list|get|find)\s+(?:all\s+)?(?:successful|passed)\s+test\s*runs?',
                'handler': self._handle_successful_tests
            },
            
            # Integration queries
            {
                'pattern': r'(?:which|what|show|list)\s+integrations?\s+(?:are\s+)?inactive',
                'handler': self._handle_inactive_integrations
            },
            {
                'pattern': r'(?:show|list|get)\s+(?:all\s+)?integrations?\s+(?:by\s+)?status',
                'handler': self._handle_integrations_by_status
            },
            
            # Agent queries
            {
                'pattern': r'(?:show|list|get|find)\s+(?:all\s+)?agents?\s+(?:using|with|in)\s+(\w+)\s+language',
                'handler': self._handle_agents_by_language
            },
            {
                'pattern': r'(?:show|list|get)\s+(?:all\s+)?agents?',
                'handler': self._handle_all_agents
            },
            
            # Workspace queries
            {
                'pattern': r'(?:show|list|get)\s+(?:all\s+)?workspaces?',
                'handler': self._handle_all_workspaces
            },
            {
                'pattern': r'workspaces?\s+(?:by\s+)?plan',
                'handler': self._handle_workspaces_by_plan
            },
            
            # Count queries
            {
                'pattern': r'(?:how many|count)\s+(\w+)',
                'handler': self._handle_count
            },
            
            # Error source queries
            {
                'pattern': r'errors?\s+(?:by\s+)?source',
                'handler': self._handle_errors_by_source
            },
            
            # Agent runs
            {
                'pattern': r'agent\s+runs?\s+(?:by\s+)?status',
                'handler': self._handle_agent_runs_status
            },
            
            # Billing/Usage
            {
                'pattern': r'(?:billing|usage|cost)\s+(?:by\s+)?workspace',
                'handler': self._handle_billing_by_workspace
            },
            {
                'pattern': r'(?:top|highest)\s+(\d+)\s+(?:token|cost|usage)',
                'handler': self._handle_top_usage
            },
        ]
    
    def parse_question(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse natural language question and return SQL query
        Returns: (sql_query, explanation)
        """
        question = question.lower().strip()
        
        # Try each pattern
        for pattern_info in self.patterns:
            match = re.search(pattern_info['pattern'], question, re.IGNORECASE)
            if match:
                try:
                    sql, explanation = pattern_info['handler'](match, question)
                    return sql, explanation
                except Exception as e:
                    continue
        
        # If no pattern matches, try keyword-based approach
        return self._keyword_based_query(question)
    
    def _handle_top_errors(self, match, question):
        """Handle 'top N errors for last X days' queries"""
        limit = match.group(1)
        time_value = match.group(2)
        time_unit = match.group(3)
        
        time_filter = self._get_time_filter(time_value, time_unit)
        
        sql = f"""
        SELECT code, message, source, COUNT(*) as error_count 
        FROM errors 
        WHERE created_at >= {time_filter}
        GROUP BY code, message, source 
        ORDER BY error_count DESC 
        LIMIT {limit}
        """
        
        explanation = f"Finding top {limit} errors from the last {time_value} {time_unit}(s)"
        return sql.strip(), explanation
    
    def _handle_errors_timeframe(self, match, question):
        """Handle 'show errors for last X days' queries"""
        time_value = match.group(1)
        time_unit = match.group(2)
        
        time_filter = self._get_time_filter(time_value, time_unit)
        
        sql = f"""
        SELECT * 
        FROM errors 
        WHERE created_at >= {time_filter}
        ORDER BY created_at DESC
        """
        
        explanation = f"Showing all errors from the last {time_value} {time_unit}(s)"
        return sql.strip(), explanation
    
    def _handle_failed_tests(self, match, question):
        """Handle failed test runs queries"""
        time_value = match.group(1)
        time_unit = match.group(2)
        
        time_filter = self._get_time_filter(time_value, time_unit)
        
        sql = f"""
        SELECT tr.*, a.name as agent_name 
        FROM test_runs tr 
        JOIN agents a ON tr.agent_id = a.id 
        WHERE tr.result = 'fail' 
        AND tr.created_at >= {time_filter}
        ORDER BY tr.created_at DESC
        """
        
        explanation = f"Finding failed test runs from the last {time_value} {time_unit}(s)"
        return sql.strip(), explanation
    
    def _handle_successful_tests(self, match, question):
        """Handle successful test runs queries"""
        sql = """
        SELECT tr.*, a.name as agent_name 
        FROM test_runs tr 
        JOIN agents a ON tr.agent_id = a.id 
        WHERE tr.result = 'pass' 
        ORDER BY tr.created_at DESC
        """
        
        explanation = "Finding all successful test runs"
        return sql.strip(), explanation
    
    def _handle_inactive_integrations(self, match, question):
        """Handle inactive integrations queries"""
        sql = """
        SELECT i.*, w.name as workspace_name 
        FROM integrations i 
        JOIN workspaces w ON i.workspace_id = w.id 
        WHERE i.status = 'inactive'
        ORDER BY i.created_at DESC
        """
        
        explanation = "Finding all inactive integrations"
        return sql.strip(), explanation
    
    def _handle_integrations_by_status(self, match, question):
        """Handle integrations by status queries"""
        sql = """
        SELECT type, status, COUNT(*) as count 
        FROM integrations 
        GROUP BY type, status 
        ORDER BY type, status
        """
        
        explanation = "Grouping integrations by type and status"
        return sql.strip(), explanation
    
    def _handle_agents_by_language(self, match, question):
        """Handle agents by language queries"""
        language_name = match.group(1).lower()
        language_code = self.languages.get(language_name, language_name[:2])
        
        sql = f"""
        SELECT a.*, w.name as workspace_name 
        FROM agents a 
        JOIN workspaces w ON a.workspace_id = w.id 
        WHERE a.language = '{language_code}'
        ORDER BY a.created_at DESC
        """
        
        explanation = f"Finding all agents using {language_name} language"
        return sql.strip(), explanation
    
    def _handle_all_agents(self, match, question):
        """Handle show all agents queries"""
        sql = """
        SELECT a.*, w.name as workspace_name 
        FROM agents a 
        JOIN workspaces w ON a.workspace_id = w.id 
        ORDER BY a.created_at DESC
        """
        
        explanation = "Listing all agents"
        return sql.strip(), explanation
    
    def _handle_all_workspaces(self, match, question):
        """Handle show all workspaces queries"""
        sql = """
        SELECT * 
        FROM workspaces 
        ORDER BY created_at DESC
        """
        
        explanation = "Listing all workspaces"
        return sql.strip(), explanation
    
    def _handle_workspaces_by_plan(self, match, question):
        """Handle workspaces by plan queries"""
        sql = """
        SELECT plan, COUNT(*) as count 
        FROM workspaces 
        GROUP BY plan 
        ORDER BY count DESC
        """
        
        explanation = "Grouping workspaces by plan type"
        return sql.strip(), explanation
    
    def _handle_count(self, match, question):
        """Handle count queries"""
        entity = match.group(1).lower()
        
        # Find matching table
        table = None
        for table_name in self.tables.keys():
            if entity in table_name or table_name.startswith(entity):
                table = table_name
                break
        
        if not table:
            return None, None
        
        sql = f"SELECT COUNT(*) as count FROM {table}"
        explanation = f"Counting total {entity}"
        return sql.strip(), explanation
    
    def _handle_errors_by_source(self, match, question):
        """Handle errors by source queries"""
        sql = """
        SELECT source, COUNT(*) as count 
        FROM errors 
        GROUP BY source 
        ORDER BY count DESC
        """
        
        explanation = "Grouping errors by source"
        return sql.strip(), explanation
    
    def _handle_agent_runs_status(self, match, question):
        """Handle agent runs by status queries"""
        sql = """
        SELECT a.name as agent_name, ar.status, COUNT(*) as count 
        FROM agent_runs ar 
        JOIN agents a ON ar.agent_id = a.id 
        GROUP BY a.name, ar.status 
        ORDER BY a.name, ar.status
        """
        
        explanation = "Grouping agent runs by status"
        return sql.strip(), explanation
    
    def _handle_billing_by_workspace(self, match, question):
        """Handle billing by workspace queries"""
        sql = """
        SELECT w.name as workspace_name, 
               SUM(b.total_cost_usd) as total_cost, 
               SUM(b.tokens_used) as total_tokens,
               SUM(b.calls_made) as total_calls
        FROM billing_usage b 
        JOIN workspaces w ON b.workspace_id = w.id 
        GROUP BY w.id, w.name 
        ORDER BY total_cost DESC
        """
        
        explanation = "Showing billing usage by workspace"
        return sql.strip(), explanation
    
    def _handle_top_usage(self, match, question):
        """Handle top usage queries"""
        limit = match.group(1)
        
        sql = f"""
        SELECT a.name as agent_name, 
               SUM(b.tokens_used) as total_tokens,
               SUM(b.total_cost_usd) as total_cost
        FROM billing_usage b 
        JOIN agents a ON b.agent_id = a.id 
        GROUP BY a.name 
        ORDER BY total_tokens DESC 
        LIMIT {limit}
        """
        
        explanation = f"Finding top {limit} agents by token usage"
        return sql.strip(), explanation
    
    def _keyword_based_query(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """Fallback: keyword-based query generation"""
        
        # Detect table from keywords
        table = None
        for table_name in self.tables.keys():
            if table_name.replace('_', ' ') in question or table_name in question:
                table = table_name
                break
        
        if not table:
            return None, "Could not understand the question. Try using query templates or be more specific."
        
        # Simple SELECT ALL
        sql = f"SELECT * FROM {table} LIMIT 100"
        explanation = f"Showing data from {table} table"
        
        return sql, explanation
    
    def _get_time_filter(self, value: str, unit: str) -> str:
        """Generate time filter for SQLite"""
        unit_map = {
            'hour': 'hours',
            'day': 'days',
            'week': 'days',
            'month': 'days'
        }
        
        multiplier = {
            'hour': 1,
            'day': 1,
            'week': 7,
            'month': 30
        }
        
        actual_value = int(value) * multiplier.get(unit, 1)
        actual_unit = unit_map.get(unit, 'days')
        
        return f"datetime('now', '-{actual_value} {actual_unit}')"
    
    def get_suggestions(self) -> List[str]:
        """Get list of example questions"""
        return [
            "Top 5 errors for the last 24 hours",
            "Show all failed test runs from last week",
            "Which integrations are inactive",
            "List all agents using Gujarati language",
            "Show all workspaces",
            "Workspaces by plan",
            "How many agents",
            "Errors by source",
            "Agent runs by status",
            "Billing by workspace",
            "Top 10 token users",
            "Show errors for last 7 days",
            "List all agents",
            "Show successful test runs"
        ]
