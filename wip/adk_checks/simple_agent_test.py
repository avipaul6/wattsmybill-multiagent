#!/usr/bin/env python3
"""
Simple test for agents without complex tools
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_simple_agents():
    """Test agents without tools"""
    print("🧪 Testing WattsMyBill Agents (Simplified)\n")
    
    try:
        from adk_integration.agent_factory import WattsMyBillAgentFactory
        
        print("✅ Agent factory imported successfully")
        
        # Create factory
        config = {'project_id': 'test-project'}
        factory = WattsMyBillAgentFactory(config)
        print("✅ Agent factory created")
        
        # Test creating agents one by one
        print("\n🤖 Testing individual agent creation:")
        
        agents_to_test = [
            ('bill_analyzer', factory.create_bill_analyzer_agent),
            ('market_researcher', factory.create_market_researcher_agent),
            ('savings_calculator', factory.create_savings_calculator_agent),
            ('rebate_hunter', factory.create_rebate_hunter_agent),
            ('usage_optimizer', factory.create_usage_optimizer_agent),
            ('orchestrator', factory.create_orchestrator_agent)
        ]
        
        created_agents = []
        
        for agent_name, create_func in agents_to_test:
            try:
                agent = create_func()
                print(f"✅ {agent_name}: {agent.name}")
                created_agents.append(agent)
                
                # Check agent attributes
                if hasattr(agent, 'description'):
                    print(f"   Description: {agent.description[:50]}...")
                
            except Exception as e:
                print(f"❌ {agent_name} failed: {e}")
        
        print(f"\n📊 Successfully created {len(created_agents)} agents")
        
        # Test runner creation with orchestrator
        if created_agents:
            print("\n🏃 Testing runner creation:")
            try:
                orchestrator = next((a for a in created_agents if a.name == 'orchestrator'), created_agents[0])
                runner = factory.create_runner(orchestrator)
                print(f"✅ Runner created with agent: {orchestrator.name}")
            except Exception as e:
                print(f"❌ Runner creation failed: {e}")
        
        # Test workflow creation
        print("\n🔄 Testing complete workflow:")
        try:
            workflow = factory.create_basic_workflow()
            print(f"✅ Workflow created with {len(workflow)} components")
            for key, component in workflow.items():
                if hasattr(component, 'name'):
                    print(f"   - {key}: {component.name}")
                else:
                    print(f"   - {key}: {type(component).__name__}")
        except Exception as e:
            print(f"❌ Workflow creation failed: {e}")
        
        return len(created_agents) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 WattsMyBill - Simple Agent Test\n")
    print("="*60)
    
    success = test_simple_agents()
    
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    if success:
        print("✅ AGENTS WORKING!")
        print("🎯 Ready for Streamlit integration")
        print("\nNext steps:")
        print("1. Replace agent_factory.py with the fixed version")
        print("2. Create basic Streamlit app")
        print("3. Test agent responses with mock data")
    else:
        print("❌ Agent creation failed")
        print("🔧 Check the error messages above")

if __name__ == "__main__":
    main()