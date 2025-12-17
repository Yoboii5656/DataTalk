  # Agent Platform Analytics - Natural Language SQL Interface

> Transform natural language questions into SQL queries using local AI - completely private, fast, and free.

## 🎯 Overview

A powerful Streamlit-based analytics dashboard for the Agent Platform that allows users to query their database using plain English. The system uses a local AI model (Ollama) to convert natural language questions into accurate SQL queries, providing instant insights into workspaces, agents, runs, errors, and billing data.

**Key Highlight:** 100% local AI processing - your data never leaves your machine!

## ✨ Features

### 🤖 Natural Language to SQL
- Ask questions in plain English
- Automatic SQL query generation using local AI
- Support for complex queries with JOINs and aggregations
- Real-time query execution and results

### 📊 Interactive Data Visualization
- Auto-generated charts based on query results
- Support for bar charts, line charts, pie charts, and scatter plots
- Interactive Plotly visualizations
- Customizable chart types

### 🔍 Advanced Query Features
- Query execution with performance metrics
- EXPLAIN plan analysis for optimization
- SQL syntax highlighting
- Export results to CSV/Excel/JSON

### 🏠 Local & Private
- Runs entirely on your machine
- No data sent to external APIs
- No internet required (after setup)
- Complete data privacy

### 🎨 User-Friendly Interface
- Clean, modern Streamlit UI
- 40+ example questions organized by category
- Real-time query suggestions
- Responsive design

## 🛠️ Tech Stack

**Frontend:**
- Streamlit 1.40.2 - Interactive web interface
- Plotly - Data visualization
- Pandas - Data manipulation

**Backend:**
- Python 3.12+
- SQLAlchemy - Database ORM
- SQLite - Database engine

**AI/ML:**
- Ollama - Local LLM runtime
- Mistral Model - Fast and accurate SQL generation
- ChromaDB - Vector storage (not currently used)

**Development:**
- Python Virtual Environment
- python-dotenv - Environment configuration

## 📋 Prerequisites

- **Python 3.12+** installed
- **Ollama** installed and running
- **8GB+ RAM** recommended for optimal performance
- **Windows/Mac/Linux** compatible

## 🚀 Quick Start

### 1. Install Ollama

Download and install from: https://ollama.ai

```bash
# Pull the Mistral model (recommended for speed)
ollama pull mistral
```

### 2. Clone & Setup

```bash
# Navigate to project directory
cd c:/Users/Manav/OneDrive/Desktop/tp

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` file:
```bash
DATABASE_URL=sqlite:///c:/Users/Manav/OneDrive/Desktop/tp/agent_platform.db
OLLAMA_MODEL=mistral
```

### 4. Run the Application

```bash
streamlit run inten/app.py
```

The app will open at: **http://localhost:5000**

## 📖 How to Use

### Basic Query
1. Type your question in plain English
2. Click "🚀 Run Query"
3. View results and auto-generated charts

### Example Questions

**Workspace Analytics:**
- "Show all workspaces and their plans"
- "Which workspaces are on enterprise plan?"
- "Count agents per workspace"

**Agent Insights:**
- "Show all agents using Hindi language"
- "List all Gujarati and Tamil agents"
- "How many agents use each language?"

**Error Analysis:**
- "Top 5 error codes from last week"
- "Show all errors from integration source"

**Billing & Usage:**
- "Total billing cost by workspace"
- "Show top 5 workspaces by total cost"
- "Billing usage for last 30 days"

## 📁 Project Structure

```
tp/
├── .env                          # Environment configuration
├── agent_platform.db             # SQLite database (1.3 MB)
├── database_export.txt           # Database export for reference
│
├── inten/                        # Main application
│   ├── .streamlit/
│   │   └── config.toml           # Streamlit config (port 5000)
│   │
│   ├── app.py                    # Main Streamlit application (26 KB)
│   ├── ollama_nl_sql.py          # Local AI NL-to-SQL (15 KB)
│   ├── local_nl_sql.py           # Pattern matching fallback (16 KB)
│   ├── schema_data.py            # Database schema definitions
│   │
│   └── database/                 # Database utilities
│       ├── schema.py             # SQLAlchemy ORM models
│       └── seed_data.py          # Data seeding script
│
└── venv/                         # Python virtual environment
```

## 🗄️ Database Schema

The application works with a multi-tenant agent platform database containing:

**Core Tables:**
- `workspaces` - Customer accounts (10 workspaces)
- `users` - Platform users (39 users)
- `agents` - Voice agents (43 agents)
- `integrations` - External integrations (HubSpot, Zoho, Twilio, etc.)

**Execution Tables:**
- `agent_runs` - Execution history
- `test_runs` - Test results
- `run_logs` - Detailed logs
- `errors` - Error tracking

**Analytics:**
- `billing_usage` - Usage metrics and costs
- `audit_events` - Change tracking

**Supported Languages:** English, Hindi, Gujarati, Tamil, Telugu, Marathi, Bengali, Kannada, Malayalam, Punjabi

## 🎯 How It Works

1. **User Input:** You type a question in natural language
2. **AI Processing:** Local AI (Ollama/Mistral) analyzes the question
3. **Schema Context:** AI references your database schema
4. **SQL Generation:** Generates accurate SQLite query
5. **Validation:** Ensures query is SELECT-only (read-only)
6. **Execution:** Runs query against your database
7. **Visualization:** Auto-generates charts from results
8. **Display:** Shows data table and visualizations

## ⚙️ Configuration

### Changing AI Model

Edit `.env`:
```bash
# Fast models
OLLAMA_MODEL=mistral        # Recommended (2-5s)
OLLAMA_MODEL=phi            # Very fast (1-3s)

# Slower but more accurate
OLLAMA_MODEL=llama3.1       # Slow (10-30s)
OLLAMA_MODEL=deepseek-coder # Good for SQL (3-6s)
```

### Changing Port

Edit `.streamlit/config.toml`:
```toml
[server]
port = 5000  # Change to your preferred port
```

## 🔒 Security & Privacy

- ✅ **Local Processing:** All AI processing happens on your machine
- ✅ **Read-Only:** Only SELECT queries allowed
- ✅ **No External APIs:** No data sent to third parties
- ✅ **Sandboxed:** SQLAlchemy prevents SQL injection
- ✅ **Private Data:** Database never leaves your computer

## 🚀 Performance

**Query Speed:**
- First query: 5-10 seconds (loads AI model)
- Subsequent: 2-5 seconds (model in memory)

**Optimization Tips:**
- Use Mistral model (fastest)
- Keep Ollama running (`ollama run mistral`)
- 16GB RAM recommended for best performance
- SSD storage helps with database queries

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve
```

### Model Not Found
```bash
# Pull the model
ollama pull mistral
```

### Slow Queries
- Switch to faster model (`mistral` or `phi`)
- Ensure Ollama is running
- Close other applications to free RAM

### Column Name Errors
- Schema is auto-synced with database
- Check `.env` database path is correct
- Verify database file exists

## 📊 Example Use Cases

### Business Intelligence
- Track workspace growth and churn
- Analyze agent usage patterns
- Monitor error trends
- Billing analysis and forecasting

### Operations
- Identify failing agents
- Debug integration issues
- Monitor system health
- Track API usage

### Product Analytics
- Language distribution analysis
- Feature adoption tracking
- Performance metrics
- User behavior analysis

## 🔄 Updates & Maintenance

**Database Export:**
```bash
python export_database.py
```
Creates `database_export.txt` with readable data snapshot.

**Update Dependencies:**
```bash
pip install --upgrade streamlit plotly pandas
```

## 🤝 Contributing

This is a personal project for the Agent Platform analytics. To extend:

1. Add new example questions in `ollama_nl_sql.py`
2. Update schema in `schema_data.py` if database changes
3. Customize visualizations in `app.py`

## 📝 License

Private project - All rights reserved

## 👤 Author

**Manav**
- Platform: Agent Platform Analytics
- Location: India
- Tech Stack: Python, Streamlit, Ollama AI

## 🙏 Acknowledgments

- **Ollama** - Local LLM runtime
- **Mistral** - Fast and accurate AI model
- **Streamlit** - Beautiful Python web apps
- **Plotly** - Interactive visualizations

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Verify Ollama is running: `ollama list`
3. Check database connection in `.env`
4. Review example questions for syntax

---

**Built with ❤️ using Local AI - 100% Private & Free**

*Last Updated: December 2025*
