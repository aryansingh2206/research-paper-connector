# How to Run the Research Paper Idea Connector

This document provides complete instructions for running the project from scratch.

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/research-paper-connector.git
cd research-paper-connector

# 2. Start everything with Docker
docker-compose up -d

# 3. Load sample papers
docker-compose exec app python scripts/ingest_papers.py data/sample_papers/

# 4. Open browser
open http://localhost:8501  # or visit manually
```

**That's it!** The system is now running with sample papers loaded.

---

## 🐳 Running with Docker (Recommended)

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually included with Docker Desktop)

### Step-by-Step

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/research-paper-connector.git
cd research-paper-connector
```

2. **Configure environment (optional)**
```bash
cp .env.example .env
# Edit .env if you want to customize settings
```

3. **Start all services**
```bash
docker-compose up -d
```

This starts:
- **Endee** vector database on port 3000
- **Streamlit** application on port 8501

4. **Wait for services to be ready** (about 30 seconds)
```bash
# Check status
docker-compose ps

# Should show both services as "Up"
```

5. **Verify setup**
```bash
docker-compose exec app python setup_verify.py
```

6. **Ingest sample papers**
```bash
docker-compose exec app python scripts/ingest_papers.py data/sample_papers/
```

7. **Access the application**

Open your browser to: **http://localhost:8501**

### Managing Services

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Stop and remove all data
docker-compose down -v
```

---

## 💻 Running Locally (Without Docker)

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Docker (only for Endee database)

### Step-by-Step

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/research-paper-connector.git
cd research-paper-connector
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start Endee database**
```bash
docker run -d \
  --name endee \
  -p 3000:3000 \
  -v endee_data:/data \
  endee/endee:latest
```

5. **Configure environment**
```bash
cp .env.example .env
# Make sure ENDEE_HOST=localhost in .env
```

6. **Verify setup**
```bash
python setup_verify.py
```

7. **Ingest sample papers**
```bash
python scripts/ingest_papers.py data/sample_papers/
```

8. **Start the application**
```bash
streamlit run app/streamlit_app.py
```

9. **Access the application**

The browser should open automatically, or navigate to: **http://localhost:8501**

---

## 🔧 Configuration Options

### Environment Variables

Edit `.env` file to configure:

```bash
# === Endee Configuration ===
ENDEE_HOST=localhost              # Use 'endee' when running in Docker Compose
ENDEE_PORT=3000
ENDEE_COLLECTION=research_papers

# === Embedding Settings ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32           # Lower if running out of memory

# === Document Processing ===
CHUNK_SIZE=500                    # Characters per chunk
CHUNK_OVERLAP=50                  # Overlap between chunks

# === Search Configuration ===
TOP_K_RESULTS=10                  # Default number of results
SIMILARITY_THRESHOLD=0.5          # Minimum similarity score

# === Optional LLM Features ===
USE_LLM_SUMMARIZATION=false       # Set to true to enable
OPENAI_API_KEY=                   # Your OpenAI key
ANTHROPIC_API_KEY=                # Or your Anthropic key
LLM_MODEL=gpt-3.5-turbo          # Or claude-3-haiku-20240307
```

---

## 📚 Usage Examples

### Web Interface Usage

1. **Upload Papers**
   - Navigate to "Upload Papers" tab
   - Drag & drop or browse for PDF/TXT files
   - Add optional metadata
   - Click "Upload and Process"

2. **Semantic Search**
   - Go to "Search" tab
   - Select "Semantic Search"
   - Enter query: e.g., "transformers and graph neural networks"
   - Adjust settings (top-k, similarity threshold)
   - Click "Search"

3. **Find Related Papers**
   - Select "Find Related Papers"
   - Enter paper ID (from search results)
   - Set number of related papers
   - Click "Find Related"

### Command Line Usage

**Ingest papers:**

```bash
# Docker
docker-compose exec app python scripts/ingest_papers.py [OPTIONS] PATHS

# Local
python scripts/ingest_papers.py [OPTIONS] PATHS

# Examples:
python scripts/ingest_papers.py data/papers/paper1.pdf --title "My Paper"
python scripts/ingest_papers.py data/papers/ --pattern "*.pdf"
python scripts/ingest_papers.py data/papers/ --reset  # Clear and re-ingest
```

**Query system:**

```bash
# Docker
docker-compose exec app python scripts/query_system.py COMMAND [OPTIONS]

# Local
python scripts/query_system.py COMMAND [OPTIONS]

# Examples:
python scripts/query_system.py search "attention mechanisms" --top-k 5
python scripts/query_system.py related paper_001 --top-k 3
python scripts/query_system.py contradictions "transformers improve accuracy"
python scripts/query_system.py search "graph networks" --summarize  # With LLM
```

---

## 📊 Complete Workflow Example

Here's a complete workflow from setup to searching:

```bash
# 1. Setup
git clone https://github.com/yourusername/research-paper-connector.git
cd research-paper-connector
docker-compose up -d

# 2. Wait for services (30 seconds)
sleep 30

# 3. Verify
docker-compose exec app python setup_verify.py

# 4. Ingest sample papers
docker-compose exec app python scripts/ingest_papers.py data/sample_papers/

# 5. Test CLI search
docker-compose exec app python scripts/query_system.py \
  search "transformers and graph learning" --top-k 5

# 6. Open web interface
open http://localhost:8501

# 7. In browser, try search:
#    Query: "attention mechanisms in vision"
#    Top-K: 10
#    Minimum Similarity: 0.5

# 8. Upload your own paper:
#    - Go to "Upload Papers" tab
#    - Select your PDF
#    - Add metadata
#    - Upload

# 9. Search your paper:
#    - Return to "Search" tab
#    - Enter relevant query
#    - See your paper in results!
```

---

## 🎯 Testing the System

### Verify Endee Connection

```bash
# Test Endee health endpoint
curl http://localhost:3000/health

# Should return 200 OK
```

### Test Embedding Generation

```bash
# Run verification script
docker-compose exec app python setup_verify.py

# Or test manually in Python:
docker-compose exec app python -c "
from src.embeddings import get_embedding_model
model = get_embedding_model()
print(f'Model loaded: {model.model_name}')
print(f'Dimension: {model.dimension}')
embedding = model.embed_text('test')
print(f'Generated embedding with {len(embedding)} dimensions')
"
```

### Test Search Functionality

```bash
# Ingest sample papers first
docker-compose exec app python scripts/ingest_papers.py data/sample_papers/

# Then test search
docker-compose exec app python scripts/query_system.py \
  search "attention" --top-k 3

# Should return results from sample papers
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
lsof -i :3000  # On Mac/Linux
netstat -ano | findstr :3000  # On Windows

# Kill the process or change port in docker-compose.yml
# Change: "3000:3000" to "3001:3000"
```

### Endee Not Starting

**Symptom:** `research-paper-endee` container keeps restarting

**Solution:**
```bash
# Check logs
docker-compose logs endee

# Remove old volume and restart
docker-compose down -v
docker-compose up -d
```

### Embedding Model Download Fails

**Error:** Connection timeout when downloading model

**Solution:**
```bash
# Pre-download the model
docker-compose exec app python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
"

# Or download manually and mount:
# 1. Download from https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
# 2. Mount in docker-compose.yml volumes section
```

### Out of Memory

**Symptom:** Process killed during ingestion

**Solution:**
```bash
# Reduce batch size in .env
EMBEDDING_BATCH_SIZE=16  # Down from 32

# Or increase Docker memory:
# Docker Desktop → Settings → Resources → Memory → Increase to 4GB+

# Restart
docker-compose restart app
```

### No Search Results

**Symptom:** Search returns 0 results even after ingestion

**Solution:**
```bash
# Verify papers were ingested
docker-compose exec app python -c "
from src.endee_client import EndeeClient
client = EndeeClient()
# Check if collection exists
print('Collection check passed')
"

# Try lowering similarity threshold
# In .env: SIMILARITY_THRESHOLD=0.3

# Restart and try again
docker-compose restart app
```

---

## 🔄 Development Mode

For active development:

```bash
# Edit docker-compose.yml to mount source as volume
# (Already configured in the provided file)

# Start in development mode
docker-compose up

# In another terminal, make code changes
# Changes in src/ and app/ will auto-reload

# View logs in real-time
docker-compose logs -f app
```

---

## 📦 Production Deployment

For production deployment:

1. **Use environment-specific .env**
```bash
cp .env.example .env.production
# Edit with production settings
```

2. **Build optimized images**
```bash
docker-compose -f docker-compose.yml build --no-cache
```

3. **Run with production settings**
```bash
docker-compose --env-file .env.production up -d
```

4. **Set up reverse proxy** (nginx example)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

5. **Enable SSL** with Let's Encrypt
```bash
certbot --nginx -d your-domain.com
```

---

## 🧹 Cleanup

### Stop and Remove Everything

```bash
# Stop services
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Remove Python Virtual Environment

```bash
# Deactivate if active
deactivate

# Remove directory
rm -rf venv/
```

---

## ✅ Success Indicators

System is working correctly when:

- ✅ Both containers show "Up" status
- ✅ Web interface loads at http://localhost:8501
- ✅ "Connected to Endee" shows green checkmark
- ✅ Sample papers ingest without errors
- ✅ Search returns relevant results
- ✅ No error messages in logs

---

## 📞 Getting Help

If you encounter issues:

1. **Check this guide** - Most common issues covered
2. **View logs** - `docker-compose logs -f`
3. **Run verification** - `setup_verify.py`
4. **Check Endee docs** - https://github.com/EndeeLabs/endee
5. **Open issue** - On GitHub with error details

---

## 🎓 Next Steps

After getting the system running:

1. Read **GETTING_STARTED.md** for detailed usage
2. Review **README.md** for architecture details
3. Explore the code in **src/** directory
4. Try advanced queries and features
5. Upload your own papers!

---

**System is ready! Start discovering research connections! 🔬🚀**
