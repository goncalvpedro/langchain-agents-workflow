# The Genesis Pipeline

A production-grade multi-agent autonomous project builder using LangGraph, OpenAI, Docker, and comprehensive observability with Grafana.

## 🎯 Overview

The Genesis Pipeline orchestrates 5 specialized AI agents to transform a raw user idea into a complete software project:

1. **Product Owner** - Creates comprehensive PRD
2. **Creative Director** - Designs brand identity (parallel)
3. **Solutions Architect** - Designs technical architecture (parallel)
4. **Lead Developer** - Generates production code (synchronization point)
5. **Growth Hacker** - Creates go-to-market strategy

## 🏗️ Architecture

```
START → Product Owner → ╔════════════════════╗
                        ║ Creative Director  ║ → Lead Developer → Growth Hacker → END
                        ║ Solutions Architect║
                        ╚════════════════════╝
                        (Parallel Execution)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key (get one at https://platform.openai.com/api-keys)
- 8GB RAM recommended
- Ports 3000 and 3100 available

### Quick Setup (3 commands)

```bash
# 1. Setup environment
chmod +x setup.sh && ./setup.sh

# 2. Add your API key to .env
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 3. Launch!
docker-compose up -d
```

Or use Make commands:
```bash
make setup
make up
make logs
```

### Local Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd genesis-pipeline

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Create required directories
mkdir -p config/dashboards logs output

# 6. Run the pipeline
python main.py
```

### Docker Production Setup

```bash
# 1. Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 2. Create config directory
mkdir -p config/dashboards

# 3. Build and start all services
docker-compose up -d

# 4. View logs
docker-compose logs -f genesis-app

# 5. Access Grafana
# Open http://localhost:3000
# Login: admin / genesis2024

# 6. Stop services
docker-compose down
```

## 📊 Observability Stack

### Services

- **Loki** (Port 3100) - Log aggregation
- **Promtail** - Log shipping from containers
- **Grafana** (Port 3000) - Visualization and monitoring

### Grafana Queries

```logql
# All pipeline logs
{service="genesis_pipeline"}

# Specific agent logs
{agent="product_owner"}

# Error logs only
{service="genesis_pipeline"} |= "error"

# Performance monitoring (execution > 10s)
{service="genesis_pipeline"} | json | execution_time > 10

# Token usage tracking
{service="genesis_pipeline"} | json | line_format "{{.agent}}: {{.tokens_used}} tokens"
```

## 📁 Project Structure

```
genesis-pipeline/
├── src/
│   ├── state.py           # State management
│   ├── nodes.py           # Agent implementations
│   ├── graph.py           # LangGraph workflow
│   └── logger_config.py   # JSON logging setup
├── config/
│   ├── loki-config.yaml
│   ├── promtail-config.yaml
│   ├── grafana-datasources.yaml
│   └── grafana-dashboards.yaml
├── output/                # Generated artifacts
│   ├── PRD.md
│   ├── brand_guide.json
│   ├── architecture.json
│   ├── marketing_plan.md
│   └── source_code/
├── logs/                  # Application logs
├── main.py               # Entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

## 🔧 Configuration

### Environment Variables

```bash
OPENAI_API_KEY=sk-...           # Required
OPENAI_MODEL=gpt-4o             # Optional, default: gpt-4o
OPENAI_TEMPERATURE=0.7          # Optional, default: 0.7
```

### Customizing Agents

Edit `src/nodes.py` to modify agent prompts or behavior:

```python
# Example: Adjust PRD format
system_prompt = """Your custom prompt here..."""
```

## 📈 Monitoring & Metrics

Each agent execution logs:

- **Agent Name** - Which agent executed
- **Execution Time** - Duration in seconds
- **Tokens Used** - OpenAI token consumption
- **Status** - success/error/running
- **Timestamp** - ISO 8601 format

### Sample Log Output

```json
{
  "timestamp": "2024-11-28T10:30:45.123Z",
  "level": "INFO",
  "service": "genesis_pipeline",
  "agent": "product_owner",
  "execution_time": 12.45,
  "tokens_used": 2847,
  "status": "success",
  "message": "Agent product_owner execution completed"
}
```

## 🧪 Testing

```bash
# Run with test query
python main.py

# Custom query
python -c "
from main import run_genesis_pipeline
import asyncio

user_idea = 'Your project idea here'
asyncio.run(run_genesis_pipeline(user_idea))
"
```

## 🎯 Output Artifacts

After execution, find generated files in `output/`:

- **PRD.md** - Product Requirements Document
- **brand_guide.json** - Brand identity and assets
- **architecture.json** - Technical architecture
- **source_code/** - Generated source files
- **marketing_plan.md** - Go-to-market strategy

## 🐛 Troubleshooting

### Quick Fixes

**Error: "proxies" keyword argument**
```bash
# Use openai==1.40.0 (already in requirements.txt)
docker-compose build --no-cache
docker-compose up -d
```

**Error: "config.yaml is a directory"**
```bash
# Fixed in latest docker-compose.yml
# Ensure you're using promtail-config.yaml mount
docker-compose down && docker-compose up -d
```

**Error: No API key**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY
# Should show: OPENAI_API_KEY=sk-...
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete guide.

### Common Issues

**Issue**: `OPENAI_API_KEY not found`
```bash
# Solution: Ensure .env file exists with valid key
cp .env.example .env
# Edit .env with your key
```

**Issue**: Docker containers won't start
```bash
# Solution: Check ports aren't in use
docker-compose down
lsof -i :3000  # Check Grafana port
lsof -i :3100  # Check Loki port
```

**Issue**: No logs in Grafana
```bash
# Solution: Check Promtail connection
docker-compose logs promtail
# Restart services
docker-compose restart promtail loki
```

## 🔒 Security Best Practices

1. **Never commit `.env`** - Use `.env.example` as template
2. **Rotate API keys** - Regularly update OpenAI keys
3. **Secure Grafana** - Change default password in production
4. **Network isolation** - Use Docker networks for service communication

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: https://docs.example.com

## 🙏 Acknowledgments

- LangGraph by LangChain
- OpenAI API
- Grafana Observability Stack

---

Built with ❤️ using LangGraph and OpenAI