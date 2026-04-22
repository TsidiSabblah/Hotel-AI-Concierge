import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key found: {api_key[:10]}...{api_key[-5:] if api_key else 'NOT FOUND'}")

if api_key and api_key.startswith("gsk_"):
    print("✅ API Key format looks correct")
    
    # Test the API
    from groq import Groq
    client = Groq(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Hello Ghana!'"}],
            max_tokens=20
        )
        print(f"✅ API works! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ API Error: {e}")
else:
    print("❌ API Key missing or invalid format")