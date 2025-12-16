# Natural Language SQL Query System

## Overview
A Streamlit application that uses Vanna.ai to convert natural language questions into SQL queries for a multi-tenant voice agent platform database.

## Features
- Natural language to SQL conversion using Vanna.ai and GPT-5
- PostgreSQL database with 12 tables storing agent platform data
- Sample data generator with realistic test data
- Query history tracking
- Database statistics dashboard

## Database Schema
The database contains 12 tables:
1. **workspaces** - Customer accounts/organizations
2. **users** - Users belonging to workspaces
3. **agents** - Voice agents with language and LLM model settings
4. **integrations** - External integrations (HubSpot, Zoho, Twilio, etc.)
5. **agent_tools** - Tools attached to agents
6. **agent_runs** - Agent execution records
7. **test_runs** - Test execution results
8. **run_logs** - Detailed logs during agent runs
9. **errors** - System and run-level failures
10. **integration_sync_logs** - Sync activity logs
11. **billing_usage** - Usage metrics per agent
12. **audit_events** - Change tracking

## Sample Questions
- "Show me all the failed test runs for agent X last week"
- "Which integrations are inactive for workspace Y?"
- "Top 5 errors for the last 24 hours?"
- "List all agents using Gujarati"
- "Show all sync logs for HubSpot integrations"
- "What tool calls caused the most failures?"

## Project Structure
- `app.py` - Main Streamlit application
- `database/` - Database models and seed data
  - `schema.py` - SQLAlchemy models for all 12 tables
  - `seed_data.py` - Sample data generator
- `vanna_setup.py` - Vanna.ai configuration and training

## Required Secrets
- `OPENAI_API_KEY` - Required for Vanna.ai natural language processing
- `DATABASE_URL` - PostgreSQL connection (auto-configured)

## Running the Application
```bash
streamlit run app.py --server.port 5000
```

## Recent Changes
- December 16, 2025: Initial setup with database schema, sample data, and Vanna.ai integration
