import requests
import json

# Your AI webhook URL
URL = "http://localhost:8000/webhook/whatsapp"

print("=" * 50)
print("🤖 Hotel AI Concierge - Test Chat")
print("=" * 50)
print("Type 'quit' to exit")
print("Type 'help' for sample questions")
print("-" * 50)

# Sample questions
samples = [
    "What time is breakfast?",
    "What is the WiFi password?",
    "When is check-out time?",
    "Do you have a swimming pool?",
    "Recommend a restaurant nearby"
]

while True:
    # Get user input
    user_input = input("\n👤 You: ").strip()
    
    if user_input.lower() == 'quit':
        print("👋 Goodbye!")
        break
    
    if user_input.lower() == 'help':
        print("\n📝 Sample questions:")
        for i, q in enumerate(samples, 1):
            print(f"   {i}. {q}")
        continue
    
    if not user_input:
        continue
    
    # Send to AI
    try:
        payload = {
            "message": {"text": user_input},
            "from": "233243371580"
        }
        
        response = requests.post(URL, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("reply", result.get("response", "No response"))
            print(f"🤖 AI: {ai_response}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure your server is running: uvicorn app.main:app --reload")