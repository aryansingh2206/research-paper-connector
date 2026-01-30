"""
Streamlit Web Interface for Research Paper Idea Connector
"""
import streamlit as st
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    EndeeClient,
    IngestionPipeline,
    SearchEngine,
    LLMSummarizer,
    settings
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Research Paper Idea Connector",
    page_icon="🔬",
    layout="wide"
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'ingestion_status' not in st.session_state:
    st.session_state.ingestion_status = []


def check_endee_connection():
    """Check if Endee is accessible"""
    try:
        client = EndeeClient()
        if client.health_check():
            return True, "✅ Connected to Endee"
        else:
            return False, "❌ Endee is not responding"
    except Exception as e:
        return False, f"❌ Cannot connect to Endee: {str(e)}"


def main():
    st.title("🔬 Research Paper Idea Connector")
    st.markdown("### Discover connections, contradictions, and unexplored intersections in research")
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Check Endee connection
        connected, status_msg = check_endee_connection()
        st.markdown(status_msg)
        
        if not connected:
            st.error("⚠️ Please ensure Endee is running. See README for instructions.")
            st.code("docker-compose up -d endee", language="bash")
        
        st.divider()
        
        st.header("Configuration")
        st.text(f"Endee: {settings.ENDEE_HOST}:{settings.ENDEE_PORT}")
        st.text(f"Collection: {settings.ENDEE_COLLECTION}")
        st.text(f"Model: {settings.EMBEDDING_MODEL}")
        
        st.divider()
        
        # LLM Settings
        st.header("LLM Summarization")
        use_llm = st.checkbox(
            "Enable LLM Summaries",
            value=settings.USE_LLM_SUMMARIZATION,
            help="Generate AI summaries of search results"
        )
        
        if use_llm:
            st.info("Requires OpenAI or Anthropic API key in .env")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "📤 Upload Papers", "📊 About"])
    
    # TAB 1: SEARCH
    with tab1:
        st.header("Search Research Papers")
        
        search_mode = st.selectbox(
            "Search Mode",
            ["Semantic Search", "Find Related Papers", "Find Contradictions"]
        )
        
        if search_mode == "Semantic Search":
            query = st.text_area(
                "Enter your query",
                placeholder="e.g., Papers connecting transformers and graph learning",
                height=100
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                top_k = st.number_input("Results", min_value=1, max_value=50, value=10)
            with col2:
                min_similarity = st.slider(
                    "Minimum Similarity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05
                )
            
            if st.button("🔍 Search", type="primary"):
                if not query:
                    st.warning("Please enter a query")
                else:
                    with st.spinner("Searching..."):
                        search_engine = SearchEngine()
                        results = search_engine.search(
                            query=query,
                            top_k=top_k,
                            min_similarity=min_similarity
                        )
                        st.session_state.search_results = results
        
        elif search_mode == "Find Related Papers":
            paper_id = st.text_input(
                "Enter Paper ID",
                placeholder="e.g., paper_001"
            )
            top_k = st.number_input("Number of Related Papers", min_value=1, max_value=20, value=5)
            
            if st.button("🔍 Find Related", type="primary"):
                if not paper_id:
                    st.warning("Please enter a paper ID")
                else:
                    with st.spinner("Finding related papers..."):
                        search_engine = SearchEngine()
                        results = search_engine.find_related_papers(
                            paper_id=paper_id,
                            top_k=top_k
                        )
                        st.session_state.search_results = results
        
        elif search_mode == "Find Contradictions":
            query = st.text_area(
                "Enter concept or finding",
                placeholder="e.g., Attention mechanisms improve model performance",
                height=100
            )
            top_k = st.number_input("Results", min_value=1, max_value=20, value=10)
            
            if st.button("🔍 Find Contradictions", type="primary"):
                if not query:
                    st.warning("Please enter a query")
                else:
                    with st.spinner("Searching for contradictions..."):
                        search_engine = SearchEngine()
                        results = search_engine.find_contradictions(
                            query=query,
                            top_k=top_k
                        )
                        st.session_state.search_results = results
        
        # Display results
        if st.session_state.search_results is not None:
            results = st.session_state.search_results
            
            st.divider()
            st.subheader(f"Results ({len(results)} matches)")
            
            if not results:
                st.info("No results found. Try adjusting your query or lowering the similarity threshold.")
            else:
                # Aggregate by paper
                search_engine = SearchEngine()
                aggregated = search_engine.aggregate_results_by_paper(results)
                
                # Display by paper
                for paper_id, matches in aggregated.items():
                    with st.expander(
                        f"📄 {matches[0].paper_title} ({len(matches)} relevant sections)",
                        expanded=True
                    ):
                        st.markdown(f"**Paper ID:** `{paper_id}`")
                        
                        # Show top matches from this paper
                        for match in matches[:3]:  # Show top 3 chunks per paper
                            st.markdown(f"**Chunk {match.chunk_index + 1}** (Similarity: {match.similarity_score:.4f})")
                            st.markdown(f"> {match.chunk_text[:500]}...")
                            st.markdown("---")
                
                # Optional LLM summary
                if use_llm:
                    if st.button("✨ Generate AI Summary"):
                        with st.spinner("Generating summary..."):
                            summarizer = LLMSummarizer()
                            result_dicts = [r.to_dict() for r in results]
                            summary = summarizer.summarize_search_results(
                                query=query if 'query' in locals() else "",
                                results=result_dicts
                            )
                            
                            if summary:
                                st.success("AI Summary:")
                                st.markdown(summary)
                            else:
                                st.warning("Could not generate summary. Check API keys.")
    
    # TAB 2: UPLOAD PAPERS
    with tab2:
        st.header("Upload Research Papers")
        
        st.markdown("""
        Upload PDF or TXT files to add them to the knowledge base.
        Papers will be processed, embedded, and stored in Endee.
        """)
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose paper files",
            type=["pdf", "txt"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s)")
            
            # Metadata inputs
            with st.form("upload_form"):
                st.subheader("Add Metadata (Optional)")
                
                default_title = st.text_input("Default Title (leave empty to use filename)")
                default_authors = st.text_input("Default Authors")
                default_year = st.number_input("Default Year", min_value=1900, max_value=2030, value=2024)
                
                submit = st.form_submit_button("📤 Upload and Process", type="primary")
                
                if submit:
                    with st.spinner("Processing papers..."):
                        pipeline = IngestionPipeline()
                        
                        # Save uploaded files temporarily
                        temp_dir = Path("./data/temp_uploads")
                        temp_dir.mkdir(parents=True, exist_ok=True)
                        
                        results = []
                        
                        for uploaded_file in uploaded_files:
                            # Save file
                            file_path = temp_dir / uploaded_file.name
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Prepare metadata
                            metadata = {
                                "title": default_title or uploaded_file.name,
                                "authors": default_authors,
                                "year": default_year,
                                "source": "user_upload"
                            }
                            
                            # Ingest
                            success = pipeline.ingest_single_paper(
                                file_path=str(file_path),
                                metadata=metadata
                            )
                            
                            results.append({
                                "filename": uploaded_file.name,
                                "success": success
                            })
                        
                        st.session_state.ingestion_status = results
        
        # Show ingestion status
        if st.session_state.ingestion_status:
            st.divider()
            st.subheader("Ingestion Status")
            
            for result in st.session_state.ingestion_status:
                if result["success"]:
                    st.success(f"✅ {result['filename']}")
                else:
                    st.error(f"❌ {result['filename']}")
    
    # TAB 3: ABOUT
    with tab3:
        st.header("About This System")
        
        st.markdown("""
        ### Research Paper Idea Connector
        
        This system helps researchers discover:
        - **Conceptual overlaps** between research papers
        - **Contradictory findings** across studies
        - **Unexplored intersections** across domains
        
        ### How It Works
        
        1. **Document Processing**: Papers are split into paragraph-level chunks
        2. **Embedding Generation**: Each chunk is converted to a 384-dimensional vector using sentence-transformers
        3. **Vector Storage**: Embeddings are stored in Endee vector database
        4. **Semantic Search**: Queries are embedded and similar vectors are retrieved using cosine similarity
        5. **Result Ranking**: Results are ranked by similarity and presented with source information
        
        ### Technology Stack
        
        - **Vector Database**: Endee (running in Docker)
        - **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
        - **Backend**: Python with FastAPI/Streamlit
        - **Optional LLM**: OpenAI GPT or Anthropic Claude
        
        ### Example Queries
        
        - "Papers connecting transformers and graph learning"
        - "Contradictory findings on attention mechanisms"
        - "Applications of reinforcement learning in robotics"
        - "Unexplored intersections between NLP and computer vision"
        """)
        
        st.divider()
        
        st.subheader("Quick Start Guide")
        
        st.markdown("""
        1. **Start Endee**: `docker-compose up -d endee`
        2. **Upload Papers**: Use the Upload tab to add research papers
        3. **Search**: Use the Search tab to query the system
        4. **Explore**: Discover connections and contradictions
        """)


if __name__ == "__main__":
    main()
