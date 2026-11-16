"""
Health Check Module

Performs startup diagnostics to ensure all components are properly configured.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import platform

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class HealthCheck:
    """System health check and diagnostics."""

    def __init__(self):
        """Initialize health checker."""
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 11:
            self.successes.append(f"Python {version_str} (compatible)")
            return True
        else:
            self.issues.append(
                f"Python {version_str} detected. Python 3.11+ required. "
                f"Download from: https://www.python.org/downloads/"
            )
            return False

    def check_ollama_connectivity(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m.get('name', 'unknown') for m in models]
                
                self.successes.append(
                    f"Ollama running with {len(models)} model(s): {', '.join(model_names[:3])}"
                )
                return True
            else:
                self.warnings.append(
                    f"Ollama responded with status {response.status_code}"
                )
                return False
                
        except ImportError:
            self.issues.append(
                "requests package not installed. Run: pip install requests"
            )
            return False
        except Exception as e:
            self.issues.append(
                f"Ollama not accessible at http://localhost:11434. "
                f"Error: {e}. "
                f"Install from: https://ollama.com/download"
            )
            return False

    def check_configured_model(self, model_name: str) -> bool:
        """Check if the configured model is available."""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                if model_name in model_names:
                    self.successes.append(f"Model '{model_name}' is available")
                    return True
                else:
                    self.issues.append(
                        f"Model '{model_name}' not found. "
                        f"Pull it with: ollama pull {model_name}"
                    )
                    return False
            else:
                return False
                
        except Exception as e:
            self.warnings.append(f"Could not verify model: {e}")
            return False

    def check_embedding_model(self) -> bool:
        """Check if sentence-transformers is available."""
        try:
            from sentence_transformers import SentenceTransformer
            self.successes.append("Sentence Transformers package available")
            return True
        except ImportError:
            self.issues.append(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            return False

    def check_chromadb(self) -> bool:
        """Check if ChromaDB is available."""
        try:
            import chromadb
            self.successes.append("ChromaDB package available")
            return True
        except ImportError:
            self.issues.append(
                "chromadb not installed. Run: pip install chromadb"
            )
            return False

    def check_knowledge_base(self, vector_db_path: Path, collection_name: str) -> bool:
        """Check if knowledge base has been built."""
        if not vector_db_path.exists():
            self.warnings.append(
                f"Knowledge base not found at {vector_db_path}. "
                f"Build it with: python scripts/build_knowledge_base.py"
            )
            return False
        
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(vector_db_path))
            
            try:
                collection = client.get_collection(name=collection_name)
                count = collection.count()
                
                if count > 0:
                    self.successes.append(
                        f"Knowledge base ready: {count} documents in '{collection_name}'"
                    )
                    return True
                else:
                    self.warnings.append(
                        f"Knowledge base exists but is empty. "
                        f"Rebuild with: python scripts/build_knowledge_base.py --rebuild"
                    )
                    return False
                    
            except Exception:
                self.warnings.append(
                    f"Collection '{collection_name}' not found. "
                    f"Build with: python scripts/build_knowledge_base.py"
                )
                return False
                
        except Exception as e:
            self.warnings.append(f"Could not check knowledge base: {e}")
            return False

    def check_database_access(self, db_path: Path) -> bool:
        """Check if database directory is writable."""
        db_dir = db_path.parent
        
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Try creating a test file
            test_file = db_dir / '.health_check_test'
            test_file.touch()
            test_file.unlink()
            
            self.successes.append(f"Database directory writable: {db_dir}")
            return True
            
        except Exception as e:
            self.issues.append(
                f"Cannot write to database directory {db_dir}: {e}"
            )
            return False

    def check_streamlit(self) -> bool:
        """Check if Streamlit is installed."""
        try:
            import streamlit
            version = streamlit.__version__
            self.successes.append(f"Streamlit {version} installed")
            return True
        except ImportError:
            self.issues.append(
                "streamlit not installed. Run: pip install streamlit"
            )
            return False

    def run_full_check(self, settings=None) -> Tuple[bool, Dict]:
        """Run all health checks.
        
        Args:
            settings: Application settings object (optional)
            
        Returns:
            Tuple of (all_passed: bool, results: dict)
        """
        print("\n" + "="*70)
        print("SYSTEM HEALTH CHECK")
        print("="*70)
        
        # System info
        print(f"\nPlatform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print(f"Architecture: {platform.machine()}")
        
        # Run checks
        checks = [
            ("Python Version", self.check_python_version()),
            ("Streamlit", self.check_streamlit()),
            ("Ollama Connectivity", self.check_ollama_connectivity()),
            ("Embedding Model Package", self.check_embedding_model()),
            ("ChromaDB Package", self.check_chromadb()),
        ]
        
        if settings:
            checks.extend([
                ("Configured LLM Model", self.check_configured_model(settings.ollama_model)),
                ("Knowledge Base", self.check_knowledge_base(settings.vector_db_dir, settings.collection_name)),
                ("Database Access", self.check_database_access(settings.db_path)),
            ])
        
        # Print results
        print("\n" + "-"*70)
        print("CHECK RESULTS")
        print("-"*70)
        
        for check_name, result in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"{status:8} {check_name}")
        
        # Print details
        if self.successes:
            print("\n[SUCCESS] Details:")
            for msg in self.successes:
                print(f"  - {msg}")
        
        if self.warnings:
            print("\n[WARNING] Issues to address:")
            for msg in self.warnings:
                print(f"  ! {msg}")
        
        if self.issues:
            print("\n[ERROR] Critical issues:")
            for msg in self.issues:
                print(f"  X {msg}")
        
        # Summary
        total = len(checks)
        passed = sum(result for _, result in checks)
        all_passed = passed == total and len(self.issues) == 0
        
        print("\n" + "="*70)
        print(f"SUMMARY: {passed}/{total} checks passed")
        
        if all_passed:
            print("[SUCCESS] System is ready!")
        elif len(self.issues) == 0:
            print("[WARNING] System functional but has warnings")
        else:
            print("[ERROR] Critical issues must be resolved")
        
        print("="*70 + "\n")
        
        return all_passed, {
            'total': total,
            'passed': passed,
            'successes': self.successes,
            'warnings': self.warnings,
            'issues': self.issues
        }


def main():
    """Run health check as standalone script."""
    from config.settings import get_settings
    
    try:
        settings = get_settings()
        checker = HealthCheck()
        all_passed, results = checker.run_full_check(settings)
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n[ERROR] Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
