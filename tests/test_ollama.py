"""
Quick test for Ollama integration and memory analysis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.memory_analyzer import MemoryAnalyzer
from modules.rag_engine import RAGEngine

print("=" * 70)
print("TESTING OLLAMA & MEMORY ANALYSIS")
print("=" * 70)

# Test memory
test_memory = """It was my last day at college. I was sitting with my friends, 
remembering all the memories we created together. I was happy, but somewhere 
inside I knew I would miss those days."""

print("\nTest Memory:")
print(test_memory)
print("\n" + "="*70)

# Initialize analyzer
print("\nInitializing Memory Analyzer...")
analyzer = MemoryAnalyzer()
print("[OK] Analyzer initialized")

# Analyze memory
print("\nAnalyzing memory with Ollama...")
analysis = analyzer.analyze_memory(test_memory)

if analysis:
    print("\n[SUCCESS] Memory analysis complete!\n")
    print(f"Title: {analysis.memory_title}")
    print(f"Summary: {analysis.summary}")
    print(f"\nPrimary Emotions: {', '.join(analysis.primary_emotions)}")
    print(f"Secondary Emotions: {', '.join(analysis.secondary_emotions)}")
    print(f"Emotional Intensity: {analysis.emotional_intensity}/10")
    print(f"\nThemes: {', '.join(analysis.themes)}")
    print(f"Context: {', '.join(analysis.context)}")
    print(f"\nGenres: {', '.join(analysis.genres)}")
    print(f"Instruments: {', '.join(analysis.instruments)}")
    print(f"Tempo: {analysis.tempo}")
    print(f"Energy: {analysis.energy}")
    print(f"Atmosphere: {analysis.atmosphere}")
    
    # Test RAG retrieval
    print("\n" + "="*70)
    print("TESTING RAG RETRIEVAL")
    print("="*70)
    
    rag_engine = RAGEngine()
    if rag_engine.is_knowledge_base_ready():
        query = analyzer.create_retrieval_query(analysis)
        print(f"\nRetrieval query: {query[:150]}...")
        
        retrieved = rag_engine.retrieve(query, top_k=3)
        print(f"\n[SUCCESS] Retrieved {len(retrieved)} documents:\n")
        
        for i, doc in enumerate(retrieved, 1):
            meta = doc.get('metadata', {})
            print(f"{i}. {meta.get('category', 'unknown').upper()}: {meta.get('topic', 'unknown')}")
            print(f"   Relevance: {doc.get('relevance_score', 0):.1%}")
            print(f"   Preview: {doc.get('text', '')[:100]}...\n")
    else:
        print("\n[WARNING] Knowledge base not ready")
    
    print("\n" + "="*70)
    print("[SUCCESS] All tests passed!")
    print("="*70)
else:
    print("\n[FAILED] Memory analysis failed")
    sys.exit(1)
