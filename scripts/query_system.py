#!/usr/bin/env python3
"""
Command-line script for querying the research paper system
"""
import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import SearchEngine, LLMSummarizer, settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Query the research paper system"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Perform semantic search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    search_parser.add_argument("--min-similarity", type=float, default=0.5, help="Minimum similarity threshold")
    search_parser.add_argument("--summarize", action="store_true", help="Generate LLM summary")
    
    # Related papers command
    related_parser = subparsers.add_parser("related", help="Find related papers")
    related_parser.add_argument("paper_id", help="Paper ID")
    related_parser.add_argument("--top-k", type=int, default=5, help="Number of related papers")
    
    # Contradictions command
    contra_parser = subparsers.add_parser("contradictions", help="Find contradictory findings")
    contra_parser.add_argument("query", help="Concept or finding to check")
    contra_parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize search engine
    search_engine = SearchEngine()
    
    # Execute command
    if args.command == "search":
        logger.info(f"Searching for: {args.query}")
        results = search_engine.search(
            query=args.query,
            top_k=args.top_k,
            min_similarity=args.min_similarity
        )
        
        # Display results
        print(search_engine.format_results(results))
        
        # Optional LLM summary
        if args.summarize:
            print("\n" + "=" * 80)
            print("AI SUMMARY")
            print("=" * 80 + "\n")
            
            summarizer = LLMSummarizer()
            result_dicts = [r.to_dict() for r in results]
            summary = summarizer.summarize_search_results(
                query=args.query,
                results=result_dicts
            )
            
            if summary:
                print(summary)
            else:
                print("Could not generate summary. Check LLM configuration.")
    
    elif args.command == "related":
        logger.info(f"Finding papers related to: {args.paper_id}")
        results = search_engine.find_related_papers(
            paper_id=args.paper_id,
            top_k=args.top_k
        )
        
        print(search_engine.format_results(results))
    
    elif args.command == "contradictions":
        logger.info(f"Finding contradictions for: {args.query}")
        results = search_engine.find_contradictions(
            query=args.query,
            top_k=args.top_k
        )
        
        print(search_engine.format_results(results))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
