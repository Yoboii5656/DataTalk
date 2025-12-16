import os
from vanna.openai import OpenAI_Chat
from vanna.vannadb import VannaDB_VectorStore

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class MyVanna(VannaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        VannaDB_VectorStore.__init__(self, vanna_model='agent-platform-model', vanna_api_key='vanna-demo-key', config=config)
        OpenAI_Chat.__init__(self, config=config)

def get_vanna_instance():
    vn = MyVanna(config={
        'api_key': OPENAI_API_KEY,
        'model': 'gpt-4o'
    })
    return vn

DDL_STATEMENTS = '''
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id UUID,
    created_at TIMESTAMP,
    plan TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active'
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    workspace_id UUID REFERENCES workspaces(id),
    role TEXT DEFAULT 'member',
    created_at TIMESTAMP
);

CREATE TABLE agents (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    name TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    llm_model TEXT DEFAULT 'gpt-4',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP
);

CREATE TABLE integrations (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    type TEXT NOT NULL,
    config JSONB,
    status TEXT DEFAULT 'active',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE agent_tools (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    tool_name TEXT NOT NULL,
    tool_config JSONB,
    created_at TIMESTAMP
);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    workspace_id UUID REFERENCES workspaces(id),
    run_type TEXT DEFAULT 'test_call',
    status TEXT DEFAULT 'success',
    duration_ms INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE test_runs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    workspace_id UUID REFERENCES workspaces(id),
    test_input TEXT,
    expected_output TEXT,
    actual_output TEXT,
    result TEXT DEFAULT 'pass',
    error_message TEXT,
    created_at TIMESTAMP
);

CREATE TABLE run_logs (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    step INTEGER,
    event_type TEXT,
    message TEXT,
    payload JSONB,
    timestamp TIMESTAMP
);

CREATE TABLE errors (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    workspace_id UUID REFERENCES workspaces(id),
    source TEXT,
    code TEXT,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);

CREATE TABLE integration_sync_logs (
    id UUID PRIMARY KEY,
    integration_id UUID REFERENCES integrations(id),
    workspace_id UUID REFERENCES workspaces(id),
    sync_type TEXT,
    status TEXT DEFAULT 'success',
    items_synced INTEGER,
    error_message TEXT,
    created_at TIMESTAMP
);

CREATE TABLE billing_usage (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    agent_id UUID REFERENCES agents(id),
    characters_generated INTEGER,
    calls_made INTEGER,
    tokens_used INTEGER,
    total_cost_usd DECIMAL(10,4),
    created_at TIMESTAMP
);

CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES users(id),
    action TEXT,
    entity TEXT,
    before JSONB,
    after JSONB,
    created_at TIMESTAMP
);
'''

DOCUMENTATION = '''
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
'''

SAMPLE_QUERIES = [
    ("Show me all the failed test runs for agent X last week", 
     "SELECT tr.*, a.name as agent_name FROM test_runs tr JOIN agents a ON tr.agent_id = a.id WHERE tr.result = 'fail' AND tr.created_at >= NOW() - INTERVAL '7 days' ORDER BY tr.created_at DESC"),
    
    ("Which integrations are inactive for workspace Y",
     "SELECT i.*, w.name as workspace_name FROM integrations i JOIN workspaces w ON i.workspace_id = w.id WHERE i.status = 'inactive'"),
    
    ("Top 5 errors for the last 24 hours",
     "SELECT code, message, source, COUNT(*) as error_count FROM errors WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY code, message, source ORDER BY error_count DESC LIMIT 5"),
    
    ("List all agents using Gujarati",
     "SELECT a.*, w.name as workspace_name FROM agents a JOIN workspaces w ON a.workspace_id = w.id WHERE a.language = 'gu'"),
    
    ("Show all sync logs for HubSpot integrations",
     "SELECT isl.*, i.type as integration_type, w.name as workspace_name FROM integration_sync_logs isl JOIN integrations i ON isl.integration_id = i.id JOIN workspaces w ON isl.workspace_id = w.id WHERE i.type = 'hubspot' ORDER BY isl.created_at DESC"),
    
    ("What tool calls caused the most failures",
     "SELECT rl.message, COUNT(*) as failure_count FROM run_logs rl JOIN agent_runs ar ON rl.run_id = ar.id WHERE rl.event_type = 'tool_call' AND ar.status = 'failed' GROUP BY rl.message ORDER BY failure_count DESC LIMIT 10"),
]

def train_vanna(vn):
    print("Training Vanna on DDL...")
    vn.train(ddl=DDL_STATEMENTS)
    
    print("Training Vanna on documentation...")
    vn.train(documentation=DOCUMENTATION)
    
    print("Training Vanna on sample queries...")
    for question, sql in SAMPLE_QUERIES:
        vn.train(question=question, sql=sql)
    
    print("Vanna training complete!")
