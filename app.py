"""
The Soundtrack of Your Life - Streamlit Application

AI-powered personal memory analysis and music recommendation system.
"""

import streamlit as st
import logging
import json
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
from modules.soundtrack_service import SoundtrackService
from modules.speech_service import SpeechService
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
                st.session_state.soundtrack_service = SoundtrackService(
                    analyzer=st.session_state.memory_analyzer,
                    rag_engine=st.session_state.rag_engine,
                    catalogue=st.session_state.catalogue,
                    recommender=st.session_state.recommendation_engine,
                    explainer=st.session_state.explanation_generator,
                    vault=st.session_state.memory_vault,
                )
                st.session_state.components_initialized = True
                logger.info("All components initialized successfully")
            except Exception as e:
                st.error(f"Failed to initialize components: {e}")
                logger.error(f"Initialization failed: {e}")
                st.stop()


def page_create_soundtrack():
    """Main page: Create Your Soundtrack."""
    st.title("The Soundtrack of Your Life")
    st.caption("Your memories. Your emotions. Your music.")
    
    st.write("""
    Describe a meaningful moment from your life, and I'll analyze the emotions and recommend music 
    that captures that feeling. Each memory is unique, and so is its soundtrack.
    """)
    
    st.write("---")
    
    # Memory input
    memory_text = st.text_area(
        "Tell me about your memory:",
        value=st.session_state.get("transcribed_memory", ""),
        height=200,
        placeholder="Example: It was my last day at college. I was sitting with my friends, remembering all the memories we created together. I was happy, but somewhere inside I knew I would miss those days...",
        max_chars=st.session_state.settings.max_memory_length
    )

    audio_input = None
    audio_input_control = getattr(st, "audio_input", None)
    if audio_input_control:
        audio_input = audio_input_control("Or record your memory", help="Recording is uploaded only after you choose to transcribe it.")
        if audio_input and st.button("Transcribe recording"):
            with st.spinner("Transcribing locally..."):
                try:
                    transcription = SpeechService().transcribe(audio_input.getvalue(), "memory.wav")
                    st.session_state.transcribed_memory = transcription["transcription"]
                    st.success("Transcription ready. Review and edit it before generating.")
                    st.rerun()
                except (ValueError, RuntimeError) as exc:
                    st.error(str(exc))
                except Exception:
                    logger.exception("Speech transcription failed")
                    st.error("The recording could not be transcribed.")

    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        generate_clicked = st.button("🎼 Generate Soundtrack", type="primary", use_container_width=True)
    
    # Generate soundtrack through the shared domain service used by the API.
    if generate_clicked:
        if not memory_text.strip():
            st.warning("Write a memory before generating a soundtrack.")
            return
        st.session_state.current_story = memory_text
        with st.spinner("Understanding the feeling, then finding its sound..."):
            try:
                st.session_state.current_result = st.session_state.soundtrack_service.generate(memory_text)
            except ValueError as exc:
                st.error(str(exc))
                return
            except RuntimeError as exc:
                st.error(str(exc))
                return
            except Exception:
                logger.exception("Soundtrack generation failed")
                st.error("The soundtrack could not be generated. Check the local setup and try again.")
                return
    
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
            
            st.write("**Primary emotions**")
            st.write(" · ".join(analysis.primary_emotions))
            
            if analysis.secondary_emotions:
                st.write("**Secondary emotions**")
                st.write(" · ".join(analysis.secondary_emotions))
        
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
            with st.container(border=True):
                st.subheader(f"{i}. {track.track_name}")
                st.caption(f"{track.artist} · {track.album or 'Album unavailable'}")
                st.progress(float(track.relevance_score), text=f"Match {track.relevance_score:.0%}")
                st.write(track.explanation)
                tags = track.genre_tags + track.mood_tags[:3]
                if tags:
                    st.caption(" · ".join(tags))
                if track.listening_url:
                    st.link_button("Open legitimate listening link", track.listening_url)
                elif track.preview_url:
                    st.audio(track.preview_url)
                else:
                    st.caption("Metadata only — no authorized preview is available.")
                feedback_cols = st.columns(4)
                for feedback_col, label, feedback_type in zip(
                    feedback_cols,
                    ("Like", "Dislike", "Save track", "Skip"),
                    ("like", "dislike", "save", "skip"),
                ):
                    with feedback_col:
                        if st.button(label, key=f"feedback_{feedback_type}_{track.track_id}"):
                            recorded = st.session_state.memory_vault.record_feedback(
                                track.track_id, feedback_type
                            )
                            if recorded:
                                st.toast(f"{label} recorded")
                            else:
                                st.error("Feedback could not be recorded")
        
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
                st.write(" · ".join(memory['emotions'][:5]))
            
            with col2:
                st.write("**Soundtrack:**")
                for rec in memory['recommendations'][:3]:
                    st.write(f"🎵 {rec['track_name']}")
                    st.write(f"   *by {rec['artist']}*")
                
                if st.button(f"🗑️ Delete", key=f"delete_{memory['id']}"):
                    if st.session_state.memory_vault.delete_memory(memory['id']):
                        st.success("Memory deleted")
                        st.rerun()


def page_preferences():
    """Preferences and local privacy controls."""
    st.title("Preferences")
    st.caption("Shape future recommendations without sending your memories to a cloud service.")
    current = st.session_state.memory_vault.get_preferences()

    preferred_languages = st.text_input(
        "Preferred languages",
        value=", ".join(current["preferred_languages"]),
        help="Separate languages with commas, for example English, Telugu, Hindi.",
    )
    preferred_genres = st.text_input(
        "Preferred genres", value=", ".join(current["preferred_genres"])
    )
    disliked_genres = st.text_input(
        "Genres to avoid", value=", ".join(current["disliked_genres"])
    )
    explicit_content = st.selectbox(
        "Explicit content", ["allow", "avoid", "unknown"],
        index=["allow", "avoid", "unknown"].index(current["explicit_content"]),
    )
    diversity = st.slider(
        "Recommendation diversity", 0.0, 1.0, float(current["diversity"]), 0.05,
        help="Higher values favor variety across artists and genres.",
    )
    if st.button("Save preferences", type="primary"):
        values = {
            "preferred_languages": [item.strip() for item in preferred_languages.split(",") if item.strip()],
            "preferred_genres": [item.strip() for item in preferred_genres.split(",") if item.strip()],
            "disliked_genres": [item.strip() for item in disliked_genres.split(",") if item.strip()],
            "explicit_content": explicit_content,
            "diversity": diversity,
        }
        if st.session_state.memory_vault.save_preferences(values):
            st.success("Preferences saved locally.")
        else:
            st.error("Preferences could not be saved.")

    st.divider()
    st.subheader("Your data")
    export = st.session_state.memory_vault.export_data()
    st.download_button(
        "Download a JSON export",
        data=json.dumps(export, ensure_ascii=False, indent=2),
        file_name="soundtrack-data-export.json",
        mime="application/json",
    )
    st.caption("Export includes saved memories, feedback, and preferences.")
    confirm_delete = st.checkbox("I understand this permanently deletes my local data")
    if st.button("Delete all personal data", disabled=not confirm_delete):
        if st.session_state.memory_vault.delete_all_data():
            st.session_state.current_result = None
            st.success("All personal data was deleted.")
            st.rerun()
        else:
            st.error("Personal data could not be deleted.")


def main():
    """Main application."""
    # Initialize
    initialize_components()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["🎼 Create Soundtrack", "🗄️ Memory Vault", "⚙️ Preferences"]
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
    elif page == "🗄️ Memory Vault":
        page_memory_vault()
    else:
        page_preferences()


if __name__ == "__main__":
    main()
