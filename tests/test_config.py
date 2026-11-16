"""
Configuration Testing

Verifies that the configuration system loads correctly and validates settings.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings, reload_settings


def test_load_settings():
    """Test that settings load without errors."""
    print("\n" + "="*70)
    print("TEST: Loading Configuration")
    print("="*70)
    
    try:
        settings = get_settings()
        print("[OK] Settings loaded successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to load settings: {e}")
        return False


def test_validate_settings():
    """Test settings validation."""
    print("\n" + "="*70)
    print("TEST: Validating Settings")
    print("="*70)
    
    try:
        settings = get_settings()
        
        # Check critical settings
        assert settings.ollama_model, "Ollama model not set"
        assert settings.embedding_model, "Embedding model not set"
        assert settings.collection_name, "Collection name not set"
        
        # Check weights
        if not settings.validate_weights_sum():
            print(f"[WARN] Scoring weights sum to {settings.total_weight:.3f} (expected ~1.0)")
        else:
            print(f"[OK] Scoring weights sum to {settings.total_weight:.3f}")
        
        # Check paths
        print(f"\nData directory: {settings.data_dir}")
        print(f"Vector DB path: {settings.vector_db_dir}")
        print(f"Database path: {settings.db_path}")
        
        print("\n[OK] All validations passed")
        return True
        
    except AssertionError as e:
        print(f"[FAIL] Validation failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error during validation: {e}")
        return False


def test_create_directories():
    """Test directory creation."""
    print("\n" + "="*70)
    print("TEST: Creating Application Directories")
    print("="*70)
    
    try:
        settings = get_settings()
        settings.ensure_directories()
        
        # Verify directories exist
        assert settings.data_dir.exists(), "Data directory not created"
        assert settings.cache_dir.exists(), "Cache directory not created"
        assert settings.vector_db_dir.exists(), "Vector DB directory not created"
        
        print(f"[OK] Data directory: {settings.data_dir}")
        print(f"[OK] Cache directory: {settings.cache_dir}")
        print(f"[OK] Vector DB directory: {settings.vector_db_dir}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to create directories: {e}")
        return False


def test_display_config():
    """Display full configuration summary."""
    print("\n" + "="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    
    try:
        settings = get_settings()
        print(settings.display_summary())
        return True
    except Exception as e:
        print(f"[FAIL] Failed to display config: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("#  THE SOUNDTRACK OF YOUR LIFE - Configuration Tests")
    print("#"*70)
    
    results = []
    
    results.append(test_load_settings())
    results.append(test_validate_settings())
    results.append(test_create_directories())
    results.append(test_display_config())
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n[SUCCESS] All configuration tests passed!")
        sys.exit(0)
    else:
        print("\n[WARNING] Some tests failed")
        sys.exit(1)
