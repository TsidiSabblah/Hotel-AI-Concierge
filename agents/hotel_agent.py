from groq import Groq
from app.config import settings
from typing import Dict, Any

class HotelAgent:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
    
    async def process_message(self, message: str, hotel_context: Dict[str, Any], guest_name: str = "Guest") -> Dict[str, Any]:
        """
        Process guest message and return response
        """
        
        hotel_name = hotel_context.get('name', 'our hotel')
        
        system_prompt = f"""You are a friendly concierge at {hotel_name} in Ghana.
        
Guest: {guest_name}
Question: {message}

Rules:
- Be warm and helpful
- Use "Sir" or "Madam"
- Keep answers short (2-3 sentences)
- Be specific with times and locations

Answer directly as the concierge:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content
            
            # Simple intent detection
            intent = "general"
            message_lower = message.lower()
            if "breakfast" in message_lower:
                intent = "breakfast"
            elif "check-out" in message_lower or "checkout" in message_lower:
                intent = "check_out"
            elif "check-in" in message_lower or "checkin" in message_lower:
                intent = "check_in"
            elif "wifi" in message_lower or "internet" in message_lower:
                intent = "wifi"
            elif "pool" in message_lower:
                intent = "pool"
            elif "spa" in message_lower:
                intent = "spa"
            elif "restaurant" in message_lower or "dinner" in message_lower:
                intent = "restaurant"
            
            return {
                "intent": intent,
                "response": ai_response,
                "needs_human": False,
                "action_needed": "none"
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return {
                "intent": "error",
                "response": f"I apologize Sir/Madam, but I'm having trouble connecting. Please call the front desk at extension 0. (Error: {str(e)[:50]})",
                "needs_human": True,
                "action_needed": "none"
            }