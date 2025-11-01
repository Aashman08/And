"""
Simple test script to verify LiteLLM setup works correctly.
Run this before starting the full service.
"""
import os
import sys
from litellm import completion

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_litellm():
    """Test basic LiteLLM functionality."""
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set in .env file")
        print("   Please add: OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    print("✅ OPENAI_API_KEY found")
    print(f"   Key starts with: {api_key[:10]}...")
    
    # Test completion call
    print("\n🧪 Testing LiteLLM completion...")
    try:
        response = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello from LiteLLM!' in exactly those words."}],
            temperature=0,
            max_tokens=20,
        )
        
        result = response.choices[0].message.content
        print(f"✅ Success! Response: {result}")
        print(f"   Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. Network connectivity")
        print("  3. OpenAI API is down")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("   LiteLLM Setup Test")
    print("=" * 50)
    print()
    
    success = test_litellm()
    
    print()
    print("=" * 50)
    if success:
        print("✅ All tests passed! LiteLLM is ready to use.")
        print("\nYou can now run:")
        print("  python -m uvicorn server:app --reload --port 8001")
    else:
        print("❌ Tests failed. Fix the issues above.")
        sys.exit(1)
    print("=" * 50)

