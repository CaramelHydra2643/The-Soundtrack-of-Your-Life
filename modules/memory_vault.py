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

    def _connect(self) -> sqlite3.Connection:
        """Open a consistently configured SQLite connection."""
        connection = sqlite3.connect(str(self.db_path), timeout=10.0)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize_database(self):
        """Create database and tables if they don't exist."""
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect and create tables
            conn = self._connect()
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id INTEGER,
                    track_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL CHECK(feedback_type IN ('like', 'dislike', 'save', 'skip')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    preferred_languages TEXT NOT NULL DEFAULT '[]',
                    preferred_genres TEXT NOT NULL DEFAULT '[]',
                    disliked_genres TEXT NOT NULL DEFAULT '[]',
                    preferred_eras TEXT NOT NULL DEFAULT '[]',
                    regional_preferences TEXT NOT NULL DEFAULT '[]',
                    explicit_content TEXT NOT NULL DEFAULT 'allow',
                    diversity REAL NOT NULL DEFAULT 0.5,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            conn = self._connect()
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
            conn = self._connect()
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
            conn = self._connect()
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
            conn = self._connect()
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
            conn = self._connect()
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

    def record_feedback(
        self,
        track_id: str,
        feedback_type: str,
        memory_id: Optional[int] = None,
    ) -> bool:
        """Persist one transparent user reaction to a recommended track."""
        if feedback_type not in {"like", "dislike", "save", "skip"} or not track_id.strip():
            return False
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO feedback (memory_id, track_id, feedback_type) VALUES (?, ?, ?)",
                    (memory_id, track_id.strip(), feedback_type),
                )
            return True
        except sqlite3.Error as exc:
            logger.error("Failed to record feedback: %s", exc)
            return False

    def get_feedback(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Return recent feedback records without exposing raw memory text."""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT id, memory_id, track_id, feedback_type, created_at "
                    "FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("Failed to retrieve feedback: %s", exc)
            return []

    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Persist single-user recommendation preferences as JSON arrays."""
        fields = {
            "preferred_languages": preferences.get("preferred_languages", []),
            "preferred_genres": preferences.get("preferred_genres", []),
            "disliked_genres": preferences.get("disliked_genres", []),
            "preferred_eras": preferences.get("preferred_eras", []),
            "regional_preferences": preferences.get("regional_preferences", []),
            "explicit_content": preferences.get("explicit_content", "allow"),
            "diversity": min(max(float(preferences.get("diversity", 0.5)), 0.0), 1.0),
        }
        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO preferences
                    (id, preferred_languages, preferred_genres, disliked_genres,
                     preferred_eras, regional_preferences, explicit_content, diversity)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                      preferred_languages=excluded.preferred_languages,
                      preferred_genres=excluded.preferred_genres,
                      disliked_genres=excluded.disliked_genres,
                      preferred_eras=excluded.preferred_eras,
                      regional_preferences=excluded.regional_preferences,
                      explicit_content=excluded.explicit_content,
                      diversity=excluded.diversity,
                      updated_at=CURRENT_TIMESTAMP
                """, (*[json.dumps(fields[key]) for key in (
                    "preferred_languages", "preferred_genres", "disliked_genres",
                    "preferred_eras", "regional_preferences"
                )], fields["explicit_content"], fields["diversity"]))
            return True
        except (sqlite3.Error, TypeError, ValueError) as exc:
            logger.error("Failed to save preferences: %s", exc)
            return False

    def get_preferences(self) -> Dict[str, Any]:
        """Return saved preferences or meaningful local defaults."""
        defaults = {
            "preferred_languages": [], "preferred_genres": [], "disliked_genres": [],
            "preferred_eras": [], "regional_preferences": [], "explicit_content": "allow",
            "diversity": 0.5,
        }
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM preferences WHERE id = 1").fetchone()
            if not row:
                return defaults
            result = dict(row)
            for key in ("preferred_languages", "preferred_genres", "disliked_genres", "preferred_eras", "regional_preferences"):
                result[key] = json.loads(result[key])
            return {key: result[key] for key in defaults}
        except (sqlite3.Error, json.JSONDecodeError) as exc:
            logger.error("Failed to retrieve preferences: %s", exc)
            return defaults

    def export_data(self) -> Dict[str, Any]:
        """Export user-owned memories, feedback, and preferences as JSON-safe data."""
        return {
            "memories": self.get_all_memories(limit=10000),
            "feedback": self.get_feedback(limit=10000),
            "preferences": self.get_preferences(),
        }

    def delete_all_data(self) -> bool:
        """Delete all single-user personal data while retaining database structure."""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM feedback")
                conn.execute("DELETE FROM memories")
                conn.execute("DELETE FROM preferences")
            return True
        except sqlite3.Error as exc:
            logger.error("Failed to delete personal data: %s", exc)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conn = self._connect()
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

