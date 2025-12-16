import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="Natural Language SQL Query",
    page_icon="🔍",
    layout="wide"
)

DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

def execute_sql(sql_query):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df, None
    except Exception as e:
        return None, str(e)

@st.cache_resource
def get_vanna():
    if not OPENAI_API_KEY:
        return None
    try:
        from vanna.openai import OpenAI_Chat
        from vanna.chromadb import ChromaDB_VectorStore
        
        class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self, config=None):
                ChromaDB_VectorStore.__init__(self, config=config)
                OpenAI_Chat.__init__(self, config=config)
        
        vn = MyVanna(config={
            'api_key': OPENAI_API_KEY,
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            'model': 'gpt-5'
        })
        
        vn.connect_to_postgres(
            host=os.environ.get("PGHOST"),
            dbname=os.environ.get("PGDATABASE"),
            user=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            port=int(os.environ.get("PGPORT", 5432))
        )
        
        return vn
    except Exception as e:
        st.error(f"Error initializing Vanna: {e}")
        return None

def train_vanna_on_schema(vn):
    ddl_statements = '''
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
    
    documentation = '''
    This database stores data for a multi-tenant voice agent platform.

    Tables and their purposes:
    - workspaces: Customer accounts/organizations. Each workspace has a plan (free/pro/enterprise) and status (active/suspended).
    - users: Users belonging to workspaces with roles (admin/member/viewer).
    - agents: Voice agents configured in each workspace. Each agent has a language code (en=English, hi=Hindi, gu=Gujarati, ta=Tamil, te=Telugu, mr=Marathi, bn=Bengali, kn=Kannada, ml=Malayalam, pa=Punjabi) and an LLM model.
    - integrations: External integrations like HubSpot, Zoho, Twilio, Plivo, Slack, or custom APIs. Status can be active, inactive, or error.
    - agent_tools: Tools attached to agents like CRM Lookup, Email Sender, HubSpot API, Slack Notifier, Web Search, Database Query, Custom Script, Calendar Check.
    - agent_runs: Records of agent executions. run_type can be live_call, test_call, cron_job, or webhook. status is success, failed, or partial.
    - test_runs: Test executions with result being pass or fail.
    - run_logs: Detailed logs during agent runs with event_type being llm_call, tool_call, user_input, or system.
    - errors: System-level and run-level failures with source being integration, agent, llm, or tool.
    - integration_sync_logs: Sync activity logs for integrations like HubSpot/Zoho data fetching. sync_type is contacts, deals, or activities.
    - billing_usage: Usage metrics per agent including characters, calls, tokens, and cost.
    - audit_events: Change tracking for who did what, with action being create, update, or delete.
    '''
    
    sample_queries = [
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
        
        ("Show all workspaces",
         "SELECT * FROM workspaces ORDER BY created_at DESC"),
        
        ("Count agents per workspace",
         "SELECT w.name as workspace_name, COUNT(a.id) as agent_count FROM workspaces w LEFT JOIN agents a ON w.id = a.workspace_id GROUP BY w.id, w.name ORDER BY agent_count DESC"),
        
        ("Show all agents with their workspace name",
         "SELECT a.name as agent_name, a.language, a.llm_model, a.status, w.name as workspace_name FROM agents a JOIN workspaces w ON a.workspace_id = w.id ORDER BY w.name, a.name"),
        
        ("Get total billing cost per workspace",
         "SELECT w.name as workspace_name, SUM(b.total_cost_usd) as total_cost FROM billing_usage b JOIN workspaces w ON b.workspace_id = w.id GROUP BY w.id, w.name ORDER BY total_cost DESC"),
    ]
    
    try:
        vn.train(ddl=ddl_statements)
        vn.train(documentation=documentation)
        for question, sql in sample_queries:
            vn.train(question=question, sql=sql)
        return True
    except Exception as e:
        st.error(f"Error training Vanna: {e}")
        return False

def get_db_stats():
    engine = get_engine()
    stats = {}
    tables = ['workspaces', 'users', 'agents', 'integrations', 'agent_tools', 
              'agent_runs', 'test_runs', 'run_logs', 'errors', 
              'integration_sync_logs', 'billing_usage', 'audit_events']
    
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[table] = result.scalar()
    return stats

st.title("🔍 Natural Language SQL Query System")
st.markdown("Ask questions about your agent platform data in plain English")

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "vanna_trained" not in st.session_state:
    st.session_state.vanna_trained = False

with st.sidebar:
    st.header("📊 Database Statistics")
    
    if st.button("Refresh Stats"):
        st.cache_data.clear()
    
    try:
        stats = get_db_stats()
        for table, count in stats.items():
            st.metric(table.replace("_", " ").title(), count)
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    
    st.divider()
    st.header("📝 Sample Questions")
    sample_questions = [
        "Show me all the failed test runs for agent X last week",
        "Which integrations are inactive?",
        "Top 5 errors for the last 24 hours",
        "List all agents using Gujarati",
        "Show all sync logs for HubSpot integrations",
        "What tool calls caused the most failures?",
        "Show all workspaces",
        "Count agents per workspace"
    ]
    
    for q in sample_questions:
        if st.button(q, key=f"sample_{q[:20]}"):
            st.session_state.current_question = q

if not OPENAI_API_KEY:
    st.warning("⚠️ OpenAI API key is required to use natural language queries. Please add the OPENAI_API_KEY secret.")
    st.info("You can still explore the database using raw SQL queries below.")
    
    st.subheader("Raw SQL Query")
    raw_sql = st.text_area("Enter SQL query:", height=100, 
                           placeholder="SELECT * FROM workspaces LIMIT 10")
    
    if st.button("Execute SQL"):
        if raw_sql:
            df, error = execute_sql(raw_sql)
            if error:
                st.error(f"Error: {error}")
            else:
                st.success(f"Query returned {len(df)} rows")
                st.dataframe(df, use_container_width=True)
else:
    vn = get_vanna()
    
    if vn and not st.session_state.vanna_trained:
        with st.spinner("Training AI on database schema..."):
            success = train_vanna_on_schema(vn)
            if success:
                st.session_state.vanna_trained = True
                st.success("AI trained successfully!")
    
    default_question = st.session_state.get("current_question", "")
    
    question = st.text_input(
        "Ask a question about your data:",
        value=default_question,
        placeholder="e.g., Show me all failed test runs from last week"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("🚀 Run Query", type="primary")
    with col2:
        show_sql = st.checkbox("Show generated SQL", value=True)
    
    if execute_button and question:
        if vn:
            with st.spinner("Generating SQL from your question..."):
                try:
                    sql = vn.generate_sql(question)
                    
                    if show_sql:
                        st.subheader("Generated SQL")
                        st.code(sql, language="sql")
                    
                    with st.spinner("Executing query..."):
                        start_time = datetime.now()
                        df, error = execute_sql(sql)
                        execution_time = (datetime.now() - start_time).total_seconds()
                    
                    if error:
                        st.error(f"Query execution error: {error}")
                    else:
                        st.success(f"Query returned {len(df)} rows in {execution_time:.3f} seconds")
                        st.dataframe(df, use_container_width=True)
                        
                        st.session_state.query_history.append({
                            "question": question,
                            "sql": sql,
                            "rows": len(df),
                            "time": execution_time,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                except Exception as e:
                    st.error(f"Error generating or executing query: {e}")
        else:
            st.error("Vanna AI is not initialized. Please check your configuration.")
    
    if st.session_state.query_history:
        st.divider()
        st.subheader("📜 Query History")
        
        for i, entry in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"[{entry['timestamp']}] {entry['question'][:50]}..."):
                st.write(f"**Question:** {entry['question']}")
                st.code(entry['sql'], language="sql")
                st.write(f"**Results:** {entry['rows']} rows in {entry['time']:.3f}s")

st.divider()
st.markdown("---")
st.caption("Powered by Vanna.ai - Natural Language to SQL")
