# Getting Started with Research Paper Idea Connector

This guide will walk you through setting up and using the Research Paper Idea Connector for the first time.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Docker and Docker Compose installed
- [ ] Python 3.10+ (if running locally)
- [ ] 4GB+ available RAM
- [ ] Terminal/command line access
- [ ] Text editor for configuration

## 🚀 Step-by-Step Setup

### Step 1: Clone and Navigate

```bash
git clone https://github.com/yourusername/research-paper-connector.git
cd research-paper-connector
```

### Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# (Optional) Edit .env with your preferred settings
# nano .env  # or use your favorite editor
```

**For basic usage**, the default settings work fine. You only need to edit `.env` if:
- You want to enable LLM summarization (requires API keys)
- You need to change Endee's host/port
- You want to adjust search parameters

### Step 3: Start Services with Docker

```bash
# Start all services (Endee + Application)
docker-compose up -d

# Check that services are running
docker-compose ps
```

You should see:
- `research-paper-endee` - Running on port 3000
- `research-paper-app` - Running on port 8501

### Step 4: Verify Setup

```bash
# Run the verification script
docker-compose exec app python setup_verify.py
```

This checks:
- ✅ Endee connectivity
- ✅ Collection initialization
- ✅ Embedding model loading
- ✅ Sample papers availability

All checks should pass (✅).

### Step 5: Load Sample Papers

```bash
# Ingest the provided sample papers
docker-compose exec app python scripts/ingest_papers.py data/sample_papers/
```

This will:
1. Process 3 sample research papers
2. Generate embeddings for each paragraph
3. Store vectors in Endee

Expected output:
```
Processing document: transformer_attention.txt
Created 12 chunks from transformer_attention.txt
Successfully ingested 12 chunks from transformer_attention.txt
...
Ingestion complete: 3/3 papers successful
```

### Step 6: Access the Web Interface

Open your browser and navigate to:
```
http://localhost:8501
```

You should see the Research Paper Idea Connector interface!

## 🎯 Your First Search

### Try These Example Queries

1. **Semantic Search Tab:**
   - Query: `"papers connecting transformers and graph learning"`
   - Top-K: `10`
   - Click "🔍 Search"

2. **Expected Results:**
   - Paragraphs from Vision Transformers discussing graph-like attention
   - Sections from Graph Neural Networks mentioning transformers
   - Cross-references between the two domains

3. **Explore Results:**
   - Click on paper expandable sections
   - Read relevant paragraphs
   - Note similarity scores

## 📤 Adding Your Own Papers

### Method 1: Web Interface

1. Go to "Upload Papers" tab
2. Click "Browse files"
3. Select PDF or TXT files
4. (Optional) Add metadata: title, authors, year
5. Click "Upload and Process"

### Method 2: Command Line

```bash
# Single file
docker-compose exec app python scripts/ingest_papers.py \
  /path/to/your/paper.pdf \
  --title "Your Paper Title" \
  --authors "Smith et al." \
  --year 2024

# Directory of papers
docker-compose exec app python scripts/ingest_papers.py \
  /path/to/papers/directory/ \
  --pattern "*.pdf"
```

### Method 3: Mount Local Directory

Edit `docker-compose.yml` to mount your papers directory:

```yaml
services:
  app:
    volumes:
      - ./data:/app/data
      - /path/to/your/papers:/app/data/my_papers  # Add this line
```

Then:
```bash
docker-compose restart app
docker-compose exec app python scripts/ingest_papers.py data/my_papers/
```

## 🔍 Advanced Search Examples

### Finding Related Papers

1. Click "Find Related Papers"
2. Enter a paper ID (e.g., from search results)
3. Set "Number of Related Papers" to `5`
4. Click "Find Related"

### Finding Contradictions

1. Click "Find Contradictions"
2. Enter a concept: `"attention mechanisms improve performance"`
3. Set results to `10`
4. Click "Find Contradictions"

### Using CLI for Queries

```bash
# Semantic search
docker-compose exec app python scripts/query_system.py \
  search "transformers in computer vision" --top-k 5

# Find related papers
docker-compose exec app python scripts/query_system.py \
  related transformer_paper --top-k 5

# Find contradictions
docker-compose exec app python scripts/query_system.py \
  contradictions "attention improves accuracy" --top-k 10
```

## 🤖 Enabling LLM Summarization (Optional)

### With OpenAI

1. Edit `.env`:
```bash
USE_LLM_SUMMARIZATION=true
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-3.5-turbo
```

2. Restart:
```bash
docker-compose restart app
```

3. In web interface, enable "Enable LLM Summaries" in sidebar

### With Anthropic

1. Edit `.env`:
```bash
USE_LLM_SUMMARIZATION=true
ANTHROPIC_API_KEY=your-key-here
LLM_MODEL=claude-3-haiku-20240307
```

2. Restart and enable as above

## 🛠️ Troubleshooting

### Endee Connection Failed

**Problem:** `❌ Endee is not responding`

**Solutions:**
```bash
# Check if Endee container is running
docker ps | grep endee

# View Endee logs
docker-compose logs endee

# Restart Endee
docker-compose restart endee

# Wait a few seconds, then check again
curl http://localhost:3000/health
```

### Embedding Model Download Slow

**Problem:** First run takes long time

**Explanation:** The sentence-transformers model (~90MB) downloads on first use. This is normal and only happens once.

**Speed up:** Pre-download model:
```bash
docker-compose exec app python -c "from src.embeddings import get_embedding_model; get_embedding_model()"
```

### Out of Memory

**Problem:** System crashes during ingestion

**Solutions:**
- Reduce `EMBEDDING_BATCH_SIZE` in `.env` (default: 32)
- Process papers in smaller batches
- Increase Docker memory allocation

### No Search Results

**Problem:** Searches return 0 results

**Checks:**
```bash
# Verify papers were ingested
docker-compose exec app python scripts/query_system.py search "test" --top-k 1

# Check collection has data
# (requires accessing Endee directly or checking logs)

# Try lowering similarity threshold
# In web UI: Move "Minimum Similarity" slider left
```

## 📊 Monitoring & Logs

### View Application Logs
```bash
docker-compose logs -f app
```

### View Endee Logs
```bash
docker-compose logs -f endee
```

### Check Resource Usage
```bash
docker stats
```

## 🔄 Maintenance

### Reset Everything

```bash
# Stop services
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Backup Your Data

```bash
# Export Endee volume
docker run --rm -v research-paper-connector_endee_data:/data \
  -v $(pwd)/backup:/backup \
  ubuntu tar czf /backup/endee_backup.tar.gz -C /data .
```

### Update the System

```bash
git pull origin main
docker-compose build
docker-compose up -d
```

## 🎓 Learning Resources

### Understanding the System

1. **Read the main README.md** - Comprehensive system documentation
2. **Explore the code** - Well-commented Python files in `src/`
3. **Check examples** - Sample papers in `data/sample_papers/`

### Endee Documentation

- Official repo: https://github.com/EndeeLabs/endee
- API reference (check repo README)

### Embedding Models

- sentence-transformers: https://www.sbert.net/
- Model card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

## ✅ Success Checklist

You're ready to use the system when you can:

- [ ] Access web interface at http://localhost:8501
- [ ] See "✅ Connected to Endee" in sidebar
- [ ] Upload a paper successfully
- [ ] Run a search and get results
- [ ] View paragraph excerpts with source information

## 🎉 Next Steps

Now that you're set up:

1. **Upload your own papers** - Build your research database
2. **Explore connections** - Find unexpected links between papers
3. **Identify gaps** - Discover research opportunities
4. **Share findings** - Export and share interesting results
5. **Customize** - Adjust settings for your workflow

## 💡 Pro Tips

1. **Better Results:** Ingest papers from multiple domains for more interesting cross-domain connections
2. **Faster Ingestion:** Use CLI batch ingestion for many papers
3. **Better Queries:** Be specific in queries - "applications of X in Y" works better than just "X"
4. **Explore Metadata:** Use filters to narrow searches by year, author, etc.
5. **Regular Backups:** If building large collection, backup Endee volume periodically

## 📞 Getting Help

- **Issues?** Check troubleshooting section above
- **Questions?** Open an issue on GitHub
- **Contributions?** Pull requests welcome!

---

**Happy exploring! 🔬**
