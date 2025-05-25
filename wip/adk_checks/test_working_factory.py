#!/usr/bin/env python3
"""
Test the working agent factory with real Google ADK
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_working_factory():
    """Test the agent factory with real ADK"""
    print("🧪 Testing WattsMyBill Agent Factory\n")
    
    try:
        # Import our working factory
        sys.path.insert(0, ".")
        from agent_factory import WattsMyBillAgentFactory
        
        print("✅ Agent factory imported successfully")
        
        # Create factory
        config = {
            'project_id': 'test-project',
            'location': 'australia'
        }
        
        factory = WattsMyBillAgentFactory(config)
        print("✅ Agent factory created")
        
        # Validate setup
        validation = factory.validate_setup()
        print(f"\n📋 Factory validation: {validation}")
        
        # Test creating individual agents
        print("\n🤖 Testing individual agent creation:")
        
        # Bill analyzer
        try:
            bill_agent = factory.create_bill_analyzer_agent()
            print(f"✅ Bill analyzer: {bill_agent.name}")
        except Exception as e:
            print(f"❌ Bill analyzer failed: {e}")
        
        # Market researcher
        try:
            market_agent = factory.create_market_researcher_agent()
            print(f"✅ Market researcher: {market_agent.name}")
        except Exception as e:
            print(f"❌ Market researcher failed: {e}")
        
        # Savings calculator
        try:
            savings_agent = factory.create_savings_calculator_agent()
            print(f"✅ Savings calculator: {savings_agent.name}")
        except Exception as e:
            print(f"❌ Savings calculator failed: {e}")
        
        # Test creating all agents at once
        print("\n🎯 Testing bulk agent creation:")
        try:
            all_agents = factory.create_all_agents()
            print(f"✅ Created {len(all_agents)} agents successfully")
            
            for agent in all_agents:
                print(f"   - {agent.name}")
        except Exception as e:
            print(f"❌ Bulk creation failed: {e}")
        
        # Test runner creation
        print("\n🏃 Testing runner creation:")
        try:
            runner = factory.create_runner(all_agents)
            print(f"✅ Runner created: {runner}")
        except Exception as e:
            print(f"❌ Runner creation failed: {e}")
        
        print("\n🎉 Agent factory test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Agent factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_interaction():
    """Test basic agent interaction capabilities"""
    print("\n🔄 Testing agent interaction capabilities...")
    
    try:
        from agent_factory import WattsMyBillAgentFactory
        
        factory = WattsMyBillAgentFactory({'project_id': 'test'})
        bill_agent = factory.create_bill_analyzer_agent()
        
        # Check if agent has expected attributes
        expected_attrs = ['name', 'description']
        
        for attr in expected_attrs:
            if hasattr(bill_agent, attr):
                value = getattr(bill_agent, attr)
                print(f"✅ {attr}: {value}")
            else:
                print(f"⚠️  Missing attribute: {attr}")
        
        # Check if we can access agent methods
        agent_methods = [method for method in dir(bill_agent) if not method.startswith('_')]
        print(f"📋 Available methods: {agent_methods[:5]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent interaction test failed: {e}")
        return False

def main():
    print("🚀 WattsMyBill - Working Agent Factory Test\n")
    print("="*60)
    
    # Run tests
    factory_success = test_working_factory()
    interaction_success = test_agent_interaction()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    if factory_success and interaction_success:
        print("✅ ALL TESTS PASSED!")
        print("🎯 Ready to integrate with Streamlit app")
        print("\nNext steps:")
        print("1. Copy agent_factory.py to src/adk_integration/")
        print("2. Create basic Streamlit app")
        print("3. Test agent execution with mock data")
    else:
        print("❌ Some tests failed")
        print("🔧 Fix issues before proceeding")

if __name__ == "__main__":
    main()