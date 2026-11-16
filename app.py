"""
The Soundtrack of Your Life - Streamlit Application

AI-powered personal memory analysis and music recommendation system.
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from modules.memory_analyzer import MemoryAnalyzer
from modules.rag_engine import RAGEngine
from modules.music_catalogue import MusicCatalogue
from modules.recommendation_engine import RecommendationEngine
from modules.explanation_generator import ExplanationGenerator
from modules.memory_vault import MemoryVault
from schemas.memory_schema import SoundtrackResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="The Soundtrack of Your Life",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.big-title {
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
}
.tagline {
    text-align: center;
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}
.emotion-tag {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    margin: 0.2rem;
    background: #e3f2fd;
    border-radius: 15px;
    font-size: 0.9rem;
}
.track-card {
    padding: 1rem;
    border-left: 4px solid #1976d2;
    background: #f5f5f5;
    margin: 1rem 0;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'current_story' not in st.session_state:
    st.session_state.current_story = ""


def initialize_components():
    """Initialize application components."""
    if 'components_initialized' not in st.session_state:
        with st.spinner("Initializing AI components..."):
            try:
                st.session_state.settings = get_settings()
                st.session_state.memory_analyzer = MemoryAnalyzer()
                st.session_state.rag_engine = RAGEngine()
                st.session_state.catalogue = MusicCatalogue()
                st.session_state.recommendation_engine = RecommendationEngine(st.session_state.catalogue)
                st.session_state.explanation_generator = ExplanationGenerator()
                st.session_state.memory_vault = MemoryVault()
                st.session_state.components_initialized = True
                logger.info("All components initialized successfully")
            except Exception as e:
                st.error(f"Failed to initialize components: {e}")
                logger.error(f"Initialization failed: {e}")
                st.stop()


def page_create_soundtrack():
    """Main page: Create Your Soundtrack."""
    st.markdown('<h1 class="big-title">🎵 The Soundtrack of Your Life</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Your memories. Your emotions. Your music.</p>', unsafe_allow_html=True)
    
    st.write("""
    Describe a meaningful moment from your life, and I'll analyze the emotions and recommend music 
    that captures that feeling. Each memory is unique, and so is its soundtrack.
    """)
    
    st.write("---")
    
    # Memory input
    memory_text = st.text_area(
        "Tell me about your memory:",
        height=200,
        placeholder="Example: It was my last day at college. I was sitting with my friends, remembering all the memories we created together. I was happy, but somewhere inside I knew I would miss those days...",
        max_chars=st.session_state.settings.max_memory_length
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        generate_clicked = st.button("🎼 Generate Soundtrack", type="primary", use_container_width=True)
    
    # Generate soundtrack
    if generate_clicked and memory_text.strip():
        st.session_state.current_story = memory_text
        
        with st.spinner("Analyzing your memory..."):
            # Step 1: Analyze memory
            analysis = st.session_state.memory_analyzer.analyze_memory(memory_text)
            
            if not analysis:
                st.error("Failed to analyze memory. Please try again.")
                return
            
            st.success("Memory analyzed!")
        
        with st.spinner("Retrieving music knowledge..."):
            # Step 2: RAG retrieval
            if st.session_state.rag_engine.is_knowledge_base_ready():
                query = st.session_state.memory_analyzer.create_retrieval_query(analysis)
                retrieved_docs = st.session_state.rag_engine.retrieve(query)
            else:
                st.warning("Knowledge base not ready. Run: python scripts/build_knowledge_base.py")
                retrieved_docs = []
        
        with st.spinner("Finding perfect tracks..."):
            # Step 3: Generate recommendations
            recommendations = st.session_state.recommendation_engine.generate_recommendations(
                analysis,
                retrieved_docs
            )
            
            if not recommendations:
                st.warning("No matching tracks found. Try describing different emotions.")
                return
        
        with st.spinner("Creating your soundtrack story..."):
            # Step 4: Generate explanation
            overall_explanation = st.session_state.explanation_generator.generate_overall_explanation(
                memory_text,
                analysis,
                recommendations,
                retrieved_docs
            )
        
        # Create result
        result = SoundtrackResult(
            memory_analysis=analysis,
            recommendations=recommendations,
            overall_explanation=overall_explanation,
            retrieved_knowledge_summary=st.session_state.rag_engine.get_retrieval_summary(retrieved_docs) if retrieved_docs else None
        )
        
        st.session_state.current_result = result
    
    # Display results
    if st.session_state.current_result:
        result = st.session_state.current_result
        analysis = result.memory_analysis
        
        st.write("---")
        st.write("## 🎭 Your Memory, Understood")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**{analysis.memory_title}**")
            st.write(analysis.summary)
            
            st.write("\n**Primary Emotions:**")
            for emotion in analysis.primary_emotions:
                st.markdown(f'<span class="emotion-tag">{emotion}</span>', unsafe_allow_html=True)
            
            if analysis.secondary_emotions:
                st.write("\n**Secondary Emotions:**")
                for emotion in analysis.secondary_emotions:
                    st.markdown(f'<span class="emotion-tag">{emotion}</span>', unsafe_allow_html=True)
        
        with col2:
            st.write("**Musical Direction:**")
            st.write(f"- **Genres:** {', '.join(analysis.genres)}")
            st.write(f"- **Instruments:** {', '.join(analysis.instruments[:4])}")
            st.write(f"- **Tempo:** {analysis.tempo}")
            st.write(f"- **Energy:** {analysis.energy}")
            st.write(f"- **Atmosphere:** {analysis.atmosphere}")
        
        st.write("---")
        st.write("## 🎵 Your Soundtrack")
        st.write(result.overall_explanation)
        
        st.write("\n### Recommended Tracks")
        
        for i, track in enumerate(result.recommendations, 1):
            with st.container():
                st.markdown(f"""
                <div class="track-card">
                    <h4>{i}. {track.track_name}</h4>
                    <p><strong>Artist:</strong> {track.artist}</p>
                    <p><strong>Relevance:</strong> {track.relevance_score:.0%}</p>
                    <p>{track.explanation}</p>
                    <p style="font-size:0.85rem; color: #666;">
                        <strong>Tags:</strong> {', '.join(track.genre_tags + track.mood_tags[:3])}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # RAG Transparency
        if result.retrieved_knowledge_summary:
            with st.expander("🔍 How AI selected this soundtrack"):
                st.write("**Music knowledge considered:**")
                for summary in result.retrieved_knowledge_summary:
                    st.write(f"- {summary}")
        
        # Save to vault
        st.write("---")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("💾 Save to Memory Vault", use_container_width=True):
                memory_id = st.session_state.memory_vault.save_memory(
                    st.session_state.current_story,
                    result
                )
                if memory_id:
                    st.success(f"Memory saved! (ID: {memory_id})")
                else:
                    st.error("Failed to save memory")


def page_memory_vault():
    """Memory Vault page."""
    st.title("🗄️ My Memory Vault")
    st.write("Browse and revisit your saved memories and their soundtracks.")
    
    # Stats
    stats = st.session_state.memory_vault.get_stats()
    st.metric("Total Memories", stats['total_memories'])
    
    if stats['total_memories'] == 0:
        st.info("No saved memories yet. Create your first soundtrack and save it!")
        return
    
    st.write("---")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Search memories", placeholder="Enter keywords...")
    
    with col2:
        emotion_filter = st.text_input("😊 Filter by emotion", placeholder="e.g., nostalgia")
    
    with col3:
        theme_filter = st.text_input("🎯 Filter by theme", placeholder="e.g., friendship")
    
    # Get memories
    if search_query:
        memories = st.session_state.memory_vault.search_memories(search_query)
    elif emotion_filter:
        memories = st.session_state.memory_vault.filter_by_emotion(emotion_filter)
    elif theme_filter:
        memories = st.session_state.memory_vault.filter_by_theme(theme_filter)
    else:
        memories = st.session_state.memory_vault.get_all_memories()
    
    st.write(f"**Showing {len(memories)} memories**")
    st.write("---")
    
    # Display memories
    for memory in memories:
        with st.expander(f"🎵 {memory['memory_title']} - {memory['created_at']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Your Memory:**")
                st.write(memory['story'][:300] + "..." if len(memory['story']) > 300 else memory['story'])
                
                st.write("\n**Emotions:**")
                for emotion in memory['emotions'][:5]:
                    st.markdown(f'<span class="emotion-tag">{emotion}</span>', unsafe_allow_html=True)
            
            with col2:
                st.write("**Soundtrack:**")
                for rec in memory['recommendations'][:3]:
                    st.write(f"🎵 {rec['track_name']}")
                    st.write(f"   *by {rec['artist']}*")
                
                if st.button(f"🗑️ Delete", key=f"delete_{memory['id']}"):
                    if st.session_state.memory_vault.delete_memory(memory['id']):
                        st.success("Memory deleted")
                        st.rerun()


def main():
    """Main application."""
    # Initialize
    initialize_components()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["🎼 Create Soundtrack", "🗄️ Memory Vault"]
    )
    
    # System info
    with st.sidebar.expander("ℹ️ System Info"):
        st.write(f"**Model:** {st.session_state.settings.ollama_model}")
        st.write(f"**Embeddings:** {st.session_state.settings.embedding_model.split('/')[-1]}")
        kb_ready = st.session_state.rag_engine.is_knowledge_base_ready()
        st.write(f"**Knowledge Base:** {'✅ Ready' if kb_ready else '❌ Not Ready'}")
        if not kb_ready:
            st.warning("Run: `python scripts/build_knowledge_base.py`")
    
    # Route to pages
    if page == "🎼 Create Soundtrack":
        page_create_soundtrack()
    else:
        page_memory_vault()


if __name__ == "__main__":
    main()
