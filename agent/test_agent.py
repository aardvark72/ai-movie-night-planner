"""
Agent Test Script

Quick validation that the agent can be imported and initialized.
Run this to verify agent configuration before deploying.
"""

def test_agent_imports():
    """Test that all agent components can be imported."""
    print("🧪 Testing agent imports...")
    
    try:
        from agent import MovieAgent, create_agent, chat
        from agent.config import AGENT_SYSTEM_PROMPT, AGENT_CONFIG
        from agent.tools import TOOLS
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_agent_configuration():
    """Test agent configuration is valid."""
    print("\n🧪 Testing agent configuration...")
    
    try:
        from agent.config import AGENT_SYSTEM_PROMPT, AGENT_CONFIG, TOOL_GUIDELINES
        
        # Verify system prompt exists
        assert len(AGENT_SYSTEM_PROMPT) > 100, "System prompt too short"
        assert "MovieMate" in AGENT_SYSTEM_PROMPT, "Missing agent name"
        
        # Verify config
        assert "model" in AGENT_CONFIG, "Missing model config"
        assert "temperature" in AGENT_CONFIG, "Missing temperature config"
        
        # Verify tool guidelines
        assert len(TOOL_GUIDELINES) == 6, f"Expected 6 tools, got {len(TOOL_GUIDELINES)}"
        
        print("✅ Configuration valid")
        print(f"   Model: {AGENT_CONFIG['model']}")
        print(f"   Temperature: {AGENT_CONFIG['temperature']}")
        print(f"   Tools configured: {len(TOOL_GUIDELINES)}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_agent_tools():
    """Test that all tools are properly defined."""
    print("\n🧪 Testing agent tools...")
    
    try:
        from agent.tools import (
            search_movies, SearchMoviesInput,
            get_group_preferences,
            add_to_watchlist, AddToWatchlistInput,
            record_rating, RecordRatingInput,
            explain_recommendation,
            compare_movies
        )
        
        tools = [
            ("search_movies", search_movies),
            ("get_group_preferences", get_group_preferences),
            ("add_to_watchlist", add_to_watchlist),
            ("record_rating", record_rating),
            ("explain_recommendation", explain_recommendation),
            ("compare_movies", compare_movies)
        ]
        
        print("✅ All 6 tools imported")
        for name, func in tools:
            print(f"   • {name}")
        
        return True
    except Exception as e:
        print(f"❌ Tools error: {e}")
        return False


def test_agent_creation():
    """Test creating an agent instance."""
    print("\n🧪 Testing agent creation...")
    
    try:
        from agent import create_agent
        
        agent = create_agent(group_id=1)
        assert agent.group_id == 1, "Group ID not set correctly"
        
        print("✅ Agent instance created successfully")
        print(f"   Default group_id: {agent.group_id}")
        return True
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return False


def run_all_tests():
    """Run all validation tests."""
    print("="*70)
    print("AGENT CONFIGURATION VALIDATION")
    print("="*70)
    
    results = []
    results.append(("Imports", test_agent_imports()))
    results.append(("Configuration", test_agent_configuration()))
    results.append(("Tools", test_agent_tools()))
    results.append(("Agent Creation", test_agent_creation()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Agent is ready to use.")
        print("\nNext steps:")
        print("  1. ✅ Agent configuration complete")
        print("  2. 🎨 Build Streamlit UI")
        print("  3. 🚀 Deploy as Databricks App V2")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()
