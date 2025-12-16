import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import json

from database.schema import (
    Base, Workspace, User, Agent, Integration, AgentTool,
    AgentRun, TestRun, RunLog, Error, IntegrationSyncLog,
    BillingUsage, AuditEvent
)

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

fake = Faker()

LANGUAGES = ["en", "hi", "gu", "ta", "te", "mr", "bn", "kn", "ml", "pa"]
LLM_MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3", "llama-2", "mistral-7b"]
PLANS = ["free", "pro", "enterprise"]
WORKSPACE_STATUSES = ["active", "suspended"]
AGENT_STATUSES = ["active", "inactive", "draft"]
INTEGRATION_TYPES = ["hubspot", "zoho", "twilio", "plivo", "slack", "custom_api"]
INTEGRATION_STATUSES = ["active", "inactive", "error"]
TOOL_NAMES = ["CRM Lookup", "Email Sender", "Calendar Check", "HubSpot API", "Slack Notifier", "Web Search", "Database Query", "Custom Script"]
RUN_TYPES = ["live_call", "test_call", "cron_job", "webhook"]
RUN_STATUSES = ["success", "failed", "partial"]
TEST_RESULTS = ["pass", "fail"]
EVENT_TYPES = ["llm_call", "tool_call", "user_input", "system"]
ERROR_SOURCES = ["integration", "agent", "llm", "tool"]
SYNC_TYPES = ["contacts", "deals", "activities"]
AUDIT_ACTIONS = ["create", "update", "delete"]
AUDIT_ENTITIES = ["agent", "integration", "tool"]

def generate_sample_data():
    session = Session()
    
    try:
        print("Clearing existing data...")
        session.query(AuditEvent).delete()
        session.query(BillingUsage).delete()
        session.query(IntegrationSyncLog).delete()
        session.query(Error).delete()
        session.query(RunLog).delete()
        session.query(TestRun).delete()
        session.query(AgentRun).delete()
        session.query(AgentTool).delete()
        session.query(Integration).delete()
        session.query(Agent).delete()
        session.query(User).delete()
        session.query(Workspace).delete()
        session.commit()
        
        print("Creating workspaces...")
        workspaces = []
        workspace_names = [
            "Acme Corp", "TechStart Inc", "Global Events", "EventPro Solutions",
            "Digital Summit", "Conference Hub", "MeetUp Masters", "Expo Connect",
            "Summit Solutions", "Event Galaxy"
        ]
        for i, name in enumerate(workspace_names):
            ws = Workspace(
                id=uuid.uuid4(),
                name=name,
                created_at=fake.date_time_between(start_date="-1y", end_date="-1m"),
                plan=random.choice(PLANS),
                status=random.choices(WORKSPACE_STATUSES, weights=[0.9, 0.1])[0]
            )
            workspaces.append(ws)
            session.add(ws)
        session.commit()
        
        print("Creating users...")
        users = []
        for ws in workspaces:
            num_users = random.randint(2, 5)
            for j in range(num_users):
                user = User(
                    id=uuid.uuid4(),
                    email=fake.email(),
                    name=fake.name(),
                    workspace_id=ws.id,
                    role="admin" if j == 0 else random.choice(["admin", "member", "viewer"]),
                    created_at=fake.date_time_between(start_date=ws.created_at, end_date="now")
                )
                users.append(user)
                session.add(user)
                if j == 0:
                    ws.owner_id = user.id
        session.commit()
        
        print("Creating agents...")
        agents = []
        agent_name_prefixes = ["Sales", "Support", "Booking", "Info", "Outreach", "Welcome", "Survey", "Feedback"]
        for ws in workspaces:
            num_agents = random.randint(2, 6)
            for _ in range(num_agents):
                agent = Agent(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    name=f"{random.choice(agent_name_prefixes)} Agent {random.randint(1, 100)}",
                    language=random.choice(LANGUAGES),
                    llm_model=random.choice(LLM_MODELS),
                    status=random.choices(AGENT_STATUSES, weights=[0.7, 0.2, 0.1])[0],
                    created_at=fake.date_time_between(start_date=ws.created_at, end_date="now")
                )
                agents.append(agent)
                session.add(agent)
        session.commit()
        
        print("Creating integrations...")
        integrations = []
        for ws in workspaces:
            num_integrations = random.randint(2, 4)
            used_types = random.sample(INTEGRATION_TYPES, num_integrations)
            for int_type in used_types:
                integration = Integration(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    type=int_type,
                    config=json.dumps({"api_key": "***", "endpoint": f"https://api.{int_type}.com"}),
                    status=random.choices(INTEGRATION_STATUSES, weights=[0.6, 0.3, 0.1])[0],
                    last_sync_at=fake.date_time_between(start_date="-30d", end_date="now") if random.random() > 0.2 else None,
                    created_at=fake.date_time_between(start_date=ws.created_at, end_date="now")
                )
                integrations.append(integration)
                session.add(integration)
        session.commit()
        
        print("Creating agent tools...")
        agent_tools = []
        for agent in agents:
            num_tools = random.randint(1, 4)
            used_tools = random.sample(TOOL_NAMES, num_tools)
            for tool_name in used_tools:
                tool = AgentTool(
                    id=uuid.uuid4(),
                    agent_id=agent.id,
                    tool_name=tool_name,
                    tool_config=json.dumps({"enabled": True, "timeout": random.randint(5, 30)}),
                    created_at=fake.date_time_between(start_date=agent.created_at, end_date="now")
                )
                agent_tools.append(tool)
                session.add(tool)
        session.commit()
        
        print("Creating agent runs...")
        agent_runs = []
        for agent in agents:
            num_runs = random.randint(10, 50)
            for _ in range(num_runs):
                started = fake.date_time_between(start_date="-30d", end_date="now")
                duration = random.randint(500, 30000)
                run = AgentRun(
                    id=uuid.uuid4(),
                    agent_id=agent.id,
                    workspace_id=agent.workspace_id,
                    run_type=random.choice(RUN_TYPES),
                    status=random.choices(RUN_STATUSES, weights=[0.7, 0.2, 0.1])[0],
                    duration_ms=duration,
                    started_at=started,
                    completed_at=started + timedelta(milliseconds=duration)
                )
                agent_runs.append(run)
                session.add(run)
        session.commit()
        
        print("Creating test runs...")
        test_runs = []
        for agent in agents:
            num_tests = random.randint(5, 20)
            for _ in range(num_tests):
                result = random.choices(TEST_RESULTS, weights=[0.6, 0.4])[0]
                test = TestRun(
                    id=uuid.uuid4(),
                    agent_id=agent.id,
                    workspace_id=agent.workspace_id,
                    test_input=fake.sentence(),
                    expected_output=fake.sentence(),
                    actual_output=fake.sentence() if result == "pass" else fake.sentence()[:20] + "...",
                    result=result,
                    error_message=fake.sentence() if result == "fail" else None,
                    created_at=fake.date_time_between(start_date="-30d", end_date="now")
                )
                test_runs.append(test)
                session.add(test)
        session.commit()
        
        print("Creating run logs...")
        for run in agent_runs[:200]:
            num_logs = random.randint(3, 10)
            for step in range(num_logs):
                log = RunLog(
                    id=uuid.uuid4(),
                    run_id=run.id,
                    step=step + 1,
                    event_type=random.choice(EVENT_TYPES),
                    message=fake.sentence(),
                    payload=json.dumps({"data": fake.word()}),
                    timestamp=run.started_at + timedelta(milliseconds=step * 100)
                )
                session.add(log)
        session.commit()
        
        print("Creating errors...")
        error_messages = [
            "Connection timeout to external API",
            "Invalid API key provided",
            "Rate limit exceeded",
            "LLM response parsing failed",
            "Tool execution timeout",
            "Database connection lost",
            "Memory limit exceeded",
            "Invalid input format",
            "Authentication failed",
            "Network unreachable"
        ]
        error_codes = ["ERR_TIMEOUT", "ERR_AUTH", "ERR_RATE_LIMIT", "ERR_PARSE", "ERR_EXEC", "ERR_DB", "ERR_MEM", "ERR_INPUT", "ERR_NET"]
        
        failed_runs = [r for r in agent_runs if r.status in ["failed", "partial"]]
        for run in failed_runs:
            num_errors = random.randint(1, 3)
            for _ in range(num_errors):
                error = Error(
                    id=uuid.uuid4(),
                    run_id=run.id,
                    workspace_id=run.workspace_id,
                    source=random.choice(ERROR_SOURCES),
                    code=random.choice(error_codes),
                    message=random.choice(error_messages),
                    error_metadata=json.dumps({"stack_trace": fake.text(max_nb_chars=100)}),
                    created_at=fake.date_time_between(start_date="-30d", end_date="now")
                )
                session.add(error)
        session.commit()
        
        print("Creating integration sync logs...")
        hubspot_integrations = [i for i in integrations if i.type == "hubspot"]
        for integration in integrations:
            num_syncs = random.randint(5, 15)
            for _ in range(num_syncs):
                status = random.choices(["success", "failed"], weights=[0.8, 0.2])[0]
                sync_log = IntegrationSyncLog(
                    id=uuid.uuid4(),
                    integration_id=integration.id,
                    workspace_id=integration.workspace_id,
                    sync_type=random.choice(SYNC_TYPES),
                    status=status,
                    items_synced=random.randint(0, 500) if status == "success" else 0,
                    error_message=fake.sentence() if status == "failed" else None,
                    created_at=fake.date_time_between(start_date="-30d", end_date="now")
                )
                session.add(sync_log)
        session.commit()
        
        print("Creating billing usage...")
        for ws in workspaces:
            ws_agents = [a for a in agents if a.workspace_id == ws.id]
            for agent in ws_agents:
                for _ in range(random.randint(3, 10)):
                    usage = BillingUsage(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        agent_id=agent.id,
                        characters_generated=random.randint(1000, 100000),
                        calls_made=random.randint(1, 100),
                        tokens_used=random.randint(100, 50000),
                        total_cost_usd=round(random.uniform(0.01, 50.00), 4),
                        created_at=fake.date_time_between(start_date="-30d", end_date="now")
                    )
                    session.add(usage)
        session.commit()
        
        print("Creating audit events...")
        for ws in workspaces:
            ws_users = [u for u in users if u.workspace_id == ws.id]
            for _ in range(random.randint(5, 15)):
                event = AuditEvent(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    user_id=random.choice(ws_users).id,
                    action=random.choice(AUDIT_ACTIONS),
                    entity=random.choice(AUDIT_ENTITIES),
                    before=json.dumps({"status": "draft"}),
                    after=json.dumps({"status": "active"}),
                    created_at=fake.date_time_between(start_date="-30d", end_date="now")
                )
                session.add(event)
        session.commit()
        
        print("\n=== Sample Data Generated Successfully! ===")
        print(f"Workspaces: {len(workspaces)}")
        print(f"Users: {len(users)}")
        print(f"Agents: {len(agents)}")
        print(f"Integrations: {len(integrations)}")
        print(f"Agent Tools: {len(agent_tools)}")
        print(f"Agent Runs: {len(agent_runs)}")
        print(f"Test Runs: {len(test_runs)}")
        print(f"Errors: {len(failed_runs) * 2} (approx)")
        
    except Exception as e:
        session.rollback()
        print(f"Error generating sample data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    generate_sample_data()
