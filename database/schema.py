import os
from sqlalchemy import create_engine, Column, String, Text, Integer, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    owner_id = Column(UUID(as_uuid=True))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    plan = Column(Text, default="free")
    status = Column(Text, default="active")
    
    users = relationship("User", back_populates="workspace")
    agents = relationship("Agent", back_populates="workspace")
    integrations = relationship("Integration", back_populates="workspace")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    role = Column(Text, default="member")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    workspace = relationship("Workspace", back_populates="users")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    name = Column(Text, nullable=False)
    language = Column(Text, default="en")
    llm_model = Column(Text, default="gpt-4")
    status = Column(Text, default="active")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    workspace = relationship("Workspace", back_populates="agents")
    tools = relationship("AgentTool", back_populates="agent")
    runs = relationship("AgentRun", back_populates="agent")
    test_runs = relationship("TestRun", back_populates="agent")

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    type = Column(Text, nullable=False)
    config = Column(JSONB)
    status = Column(Text, default="active")
    last_sync_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    workspace = relationship("Workspace", back_populates="integrations")
    sync_logs = relationship("IntegrationSyncLog", back_populates="integration")

class AgentTool(Base):
    __tablename__ = "agent_tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    tool_name = Column(Text, nullable=False)
    tool_config = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="tools")

class AgentRun(Base):
    __tablename__ = "agent_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    run_type = Column(Text, default="test_call")
    status = Column(Text, default="success")
    duration_ms = Column(Integer)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP)
    
    agent = relationship("Agent", back_populates="runs")
    logs = relationship("RunLog", back_populates="run")
    errors = relationship("Error", back_populates="run")

class TestRun(Base):
    __tablename__ = "test_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    test_input = Column(Text)
    expected_output = Column(Text)
    actual_output = Column(Text)
    result = Column(Text, default="pass")
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="test_runs")

class RunLog(Base):
    __tablename__ = "run_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))
    step = Column(Integer)
    event_type = Column(Text)
    message = Column(Text)
    payload = Column(JSONB)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    
    run = relationship("AgentRun", back_populates="logs")

class Error(Base):
    __tablename__ = "errors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    source = Column(Text)
    code = Column(Text)
    message = Column(Text)
    error_metadata = Column("metadata", JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    run = relationship("AgentRun", back_populates="errors")

class IntegrationSyncLog(Base):
    __tablename__ = "integration_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    sync_type = Column(Text)
    status = Column(Text, default="success")
    items_synced = Column(Integer)
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    integration = relationship("Integration", back_populates="sync_logs")

class BillingUsage(Base):
    __tablename__ = "billing_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    characters_generated = Column(Integer)
    calls_made = Column(Integer)
    tokens_used = Column(Integer)
    total_cost_usd = Column(DECIMAL(10, 4))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(Text)
    entity = Column(Text)
    before = Column(JSONB)
    after = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

if __name__ == "__main__":
    create_tables()
