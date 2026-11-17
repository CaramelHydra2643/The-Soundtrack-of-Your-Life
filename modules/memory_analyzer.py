"""
Memory Analysis Engine

Uses Ollama LLM to analyze personal memories and extract emotional and musical characteristics.
"""

import json
import logging
from typing import Dict, Any, Optional

import ollama
from pydantic import ValidationError

from config.settings import get_settings
from schemas.memory_schema import MemoryAnalysis

logger = logging.getLogger(__name__)


class MemoryAnalyzer:
    """Analyzes personal memories using local LLM to extract emotions and musical characteristics."""

    def __init__(self):
        """Initialize the memory analyzer with configuration."""
        self.settings = get_settings()
        self.model = self.settings.ollama_model
        self.base_url = self.settings.ollama_base_url
        self.temperature = self.settings.llm_temperature
        self.timeout = self.settings.llm_timeout
        self.max_tokens = self.settings.llm_max_tokens
        self.client = ollama.Client(host=self.base_url)

    def _create_analysis_prompt(self, memory_text: str) -> str:
        """Create a detailed prompt for memory analysis.
        
        Args:
            memory_text: The user's personal memory description
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""You are an expert at analyzing personal memories and understanding their emotional depth and musical resonance.

Analyze the following personal memory and extract its emotional and musical characteristics.

MEMORY:
\"\"\"
{memory_text}
\"\"\"

Provide your analysis as a JSON object with these fields:

1. memory_title: A short, evocative title (5-15 words)
2. summary: A brief summary capturing the essence (20-100 words)
3. primary_emotions: List of 1-3 main emotions (e.g., nostalgia, happiness, sadness, gratitude, excitement, peace, love, pride, hope)
4. secondary_emotions: List of 0-3 subtle or underlying emotions
5. emotional_intensity: Rate 1-10 (1=subtle, 10=overwhelming)
6. themes: List of 2-5 key themes (e.g., friendship, achievement, farewell, family, growth, celebration)
7. context: List of 1-5 contextual elements (e.g., college, childhood, work, travel, home)
8. genres: List of 2-4 music genres that would match (e.g., indie folk, acoustic pop, classical, ambient, jazz, soft rock)
9. instruments: List of 3-6 instruments that would capture the mood (e.g., piano, acoustic guitar, strings, flute, drums)
10. tempo: Describe the tempo (e.g., slow, moderate, fast, variable)
11. energy: Describe the energy level (e.g., low, moderate, high, dynamic)
12. atmosphere: Describe the overall musical atmosphere (20-50 words)
13. musical_description: Detailed description of musical characteristics (50-200 words)
14. language: The language most present in the memory, or null when unclear
15. cultural_context: Specific cultural or regional references, without stereotyping

IMPORTANT:
- Be authentic to the specific emotions in this memory - don't force emotions that aren't present
- Support complex, mixed emotions (e.g., happy but sad)
- Base musical recommendations on the actual emotional tone
- Return ONLY valid JSON, no other text

JSON OUTPUT:
"""
        return prompt

    def analyze_memory(self, memory_text: str, retry: bool = True) -> Optional[MemoryAnalysis]:
        """Analyze a personal memory using LLM.
        
        Args:
            memory_text: The user's memory description
            retry: Whether to retry once on JSON parsing failure
            
        Returns:
            MemoryAnalysis object if successful, None otherwise
        """
        if not memory_text or len(memory_text.strip()) < 10:
            logger.error("Memory text too short for analysis")
            return None

        if len(memory_text) > self.settings.max_memory_length:
            logger.error("Memory exceeds the configured character limit")
            return None

        prompt = self._create_analysis_prompt(memory_text)

        try:
            logger.info(f"Analyzing memory with {self.model}...")
            
            # Call Ollama
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                }
            )

            # Extract response content
            response_text = response['message']['content']
            logger.debug(f"LLM response: {response_text[:500]}...")

            # Parse JSON
            try:
                # Try to extract JSON if wrapped in markdown code blocks
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()

                analysis_dict = json.loads(response_text)
                
                # Validate with Pydantic
                analysis = MemoryAnalysis(**analysis_dict)
                logger.info("Memory analysis successful")
                return analysis

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                if retry:
                    logger.info("Retrying with explicit JSON request...")
                    return self.analyze_memory(memory_text, retry=False)
                return None

            except ValidationError as e:
                logger.error(f"Pydantic validation failed: {e}")
                if retry:
                    logger.info("Retrying after structured-output validation failure...")
                    return self.analyze_memory(memory_text, retry=False)
                return None

        except Exception as e:
            logger.error(f"Memory analysis failed: {e}")
            return None

    def create_retrieval_query(self, analysis: MemoryAnalysis) -> str:
        """Create a semantic search query from memory analysis.
        
        Args:
            analysis: Validated memory analysis
            
        Returns:
            Formatted query string for RAG retrieval
        """
        # Combine key elements into a rich query
        query_parts = []
        
        # Emotions (weighted heavily)
        emotions = analysis.primary_emotions + analysis.secondary_emotions
        if emotions:
            query_parts.append(" ".join(emotions))
        
        # Themes and context
        if analysis.themes:
            query_parts.append(" ".join(analysis.themes))
        if analysis.context:
            query_parts.append(" ".join(analysis.context))
        
        # Musical characteristics
        if analysis.genres:
            query_parts.append(" ".join(analysis.genres))
        if analysis.instruments:
            query_parts.append(" ".join(analysis.instruments))
        
        # Tempo and atmosphere
        query_parts.append(f"{analysis.tempo} tempo")
        query_parts.append(f"{analysis.energy} energy")
        query_parts.append(analysis.atmosphere)
        
        query = ", ".join(query_parts)
        logger.debug(f"Retrieval query: {query}")
        return query
