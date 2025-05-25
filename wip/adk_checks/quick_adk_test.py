#!/usr/bin/env python3
"""
Quick test to verify Google ADK imports work correctly - this is to check in case ADK changes
Run this first before proceeding with full agent implementation
"""

def test_adk_imports():
    """Test the official Google ADK imports"""
    print("🔍 Testing Google ADK v1.0 imports...")
    
    try:
        from google.adk.agents import Agent
        print("✅ google.adk.agents.Agent imported successfully")
        
        from google.adk.core import Task
        print("✅ google.adk.core.Task imported successfully")
        
        from google.adk.core import TaskResult
        print("✅ google.adk.core.TaskResult imported successfully")
        
        from google.adk.orchestration import AgentOrchestrator
        print("✅ google.adk.orchestration.AgentOrchestrator imported successfully")
        
        print("\n🎉 All Google ADK imports successful!")
        
        # Test basic agent creation
        print("\n🤖 Testing basic agent creation...")
        
        # Create a simple agent (check what parameters it expects)
        try:
            agent = Agent(name="test_agent")
            print(f"✅ Basic agent created: {agent}")
        except Exception as e:
            print(f"⚠️  Agent creation failed: {e}")
            print("   This might be normal - checking required parameters...")
        
        # Test task creation
        print("\n📋 Testing basic task creation...")
        try:
            task = Task(id="test_task")
            print(f"✅ Basic task created: {task}")
        except Exception as e:
            print(f"⚠️  Task creation failed: {e}")
            print("   This might be normal - checking required parameters...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Google ADK import failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify installation: pip install google-adk")
        print("2. Check version: pip show google-adk")
        print("3. Try reinstalling: pip uninstall google-adk && pip install google-adk")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_package_info():
    """Check the installed Google ADK package info"""
    print("\n📦 Checking Google ADK package info...")
    
    try:
        import pkg_resources
        adk_package = pkg_resources.get_distribution("google-adk")
        print(f"✅ Google ADK version: {adk_package.version}")
        print(f"   Location: {adk_package.location}")
        
        # Check what's actually in the package
        print("\n📁 Package contents:")
        try:
            import google.adk
            print(f"   google.adk module: {google.adk}")
            
            # List submodules
            import pkgutil
            for importer, modname, ispkg in pkgutil.iter_modules(google.adk.__path__, google.adk.__name__ + "."):
                print(f"   - {modname}")
                
        except Exception as e:
            print(f"   Could not inspect package contents: {e}")
        
    except Exception as e:
        print(f"❌ Could not get package info: {e}")

if __name__ == "__main__":
    print("🚀 WattsMyBill - Google ADK Import Verification\n")
    
    check_package_info()
    success = test_adk_imports()
    
    print("\n" + "="*50)
    if success:
        print("✅ READY: Google ADK imports working correctly!")
        print("   You can now proceed with agent implementation.")
    else:
        print("❌ ISSUE: Google ADK imports failed.")
        print("   Fix the ADK installation before proceeding.")
    print("="*50)