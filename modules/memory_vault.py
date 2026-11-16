"""
Memory Vault Module

Manages persistent storage of analyzed memories and recommendations using SQLite.
"""

import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import get_settings
from schemas.memory_schema import SavedMemory, SoundtrackResult

logger = logging.getLogger(__name__)


class MemoryVault:
    """Manages persistent storage of personal memories and their soundtracks."""

    def __init__(self):
        """Initialize memory vault with SQLite database."""
        self.settings = get_settings()
        self.db_path = self.settings.db_path
        self._initialize_database()

    def _initialize_database(self):
        """Create database and tables if they don't exist."""
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect and create tables
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story TEXT NOT NULL,
                    memory_title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    emotions TEXT NOT NULL,
                    themes TEXT NOT NULL,
                    musical_attributes TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster searching
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_title ON memories(memory_title)"
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def save_memory(
        self,
        story: str,
        soundtrack_result: SoundtrackResult
    ) -> Optional[int]:
        """Save a memory and its soundtrack to the vault.
        
        Args:
            story: Original memory text
            soundtrack_result: Complete soundtrack generation result
            
        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            analysis = soundtrack_result.memory_analysis
            
            # Combine all emotions
            all_emotions = analysis.primary_emotions + analysis.secondary_emotions
            
            # Prepare musical attributes
            musical_attributes = {
                'genres': analysis.genres,
                'instruments': analysis.instruments,
                'tempo': analysis.tempo,
                'energy': analysis.energy,
                'atmosphere': analysis.atmosphere,
                'musical_description': analysis.musical_description
            }
            
            # Convert recommendations to dicts
            recommendations_data = [
                {
                    'track_id': rec.track_id,
                    'track_name': rec.track_name,
                    'artist': rec.artist,
                    'genre_tags': rec.genre_tags,
                    'mood_tags': rec.mood_tags,
                    'instrument_tags': rec.instrument_tags,
                    'relevance_score': rec.relevance_score,
                    'explanation': rec.explanation,
                    'source': rec.source
                }
                for rec in soundtrack_result.recommendations
            ]
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO memories (
                    story, memory_title, summary, emotions, themes,
                    musical_attributes, recommendations, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story,
                analysis.memory_title,
                analysis.summary,
                json.dumps(all_emotions),
                json.dumps(analysis.themes),
                json.dumps(musical_attributes),
                json.dumps(recommendations_data),
                soundtrack_result.overall_explanation
            ))
            
            memory_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return None

    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all saved memories.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of memory dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                memory = {
                    'id': row['id'],
                    'story': row['story'],
                    'memory_title': row['memory_title'],
                    'summary': row['summary'],
                    'emotions': json.loads(row['emotions']),
                    'themes': json.loads(row['themes']),
                    'musical_attributes': json.loads(row['musical_attributes']),
                    'recommendations': json.loads(row['recommendations']),
                    'explanation': row['explanation'],
                    'created_at': row['created_at']
                }
                memories.append(memory)
            
            logger.info(f"Retrieved {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory dictionary or None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            memory = {
                'id': row['id'],
                'story': row['story'],
                'memory_title': row['memory_title'],
                'summary': row['summary'],
                'emotions': json.loads(row['emotions']),
                'themes': json.loads(row['themes']),
                'musical_attributes': json.loads(row['musical_attributes']),
                'recommendations': json.loads(row['recommendations']),
                'explanation': row['explanation'],
                'created_at': row['created_at']
            }
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by keyword.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching memories
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT * FROM memories
                WHERE story LIKE ? OR memory_title LIKE ? OR summary LIKE ?
                ORDER BY created_at DESC
            """, (search_pattern, search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                memory = {
                    'id': row['id'],
                    'story': row['story'],
                    'memory_title': row['memory_title'],
                    'summary': row['summary'],
                    'emotions': json.loads(row['emotions']),
                    'themes': json.loads(row['themes']),
                    'musical_attributes': json.loads(row['musical_attributes']),
                    'recommendations': json.loads(row['recommendations']),
                    'explanation': row['explanation'],
                    'created_at': row['created_at']
                }
                memories.append(memory)
            
            logger.info(f"Found {len(memories)} memories matching '{query}'")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    def filter_by_emotion(self, emotion: str) -> List[Dict[str, Any]]:
        """Filter memories by emotion.
        
        Args:
            emotion: Emotion to filter by
            
        Returns:
            List of matching memories
        """
        all_memories = self.get_all_memories()
        
        filtered = [
            memory for memory in all_memories
            if any(emotion.lower() in e.lower() for e in memory['emotions'])
        ]
        
        logger.info(f"Found {len(filtered)} memories with emotion '{emotion}'")
        return filtered

    def filter_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Filter memories by theme.
        
        Args:
            theme: Theme to filter by
            
        Returns:
            List of matching memories
        """
        all_memories = self.get_all_memories()
        
        filtered = [
            memory for memory in all_memories
            if any(theme.lower() in t.lower() for t in memory['themes'])
        ]
        
        logger.info(f"Found {len(filtered)} memories with theme '{theme}'")
        return filtered

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from the vault.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Deleted memory {memory_id}")
            else:
                logger.warning(f"Memory {memory_id} not found")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT created_at FROM memories ORDER BY created_at ASC LIMIT 1")
            oldest = cursor.fetchone()
            
            cursor.execute("SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1")
            newest = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_memories': total,
                'oldest_memory': oldest[0] if oldest else None,
                'newest_memory': newest[0] if newest else None,
                'database_path': str(self.db_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total_memories': 0}
