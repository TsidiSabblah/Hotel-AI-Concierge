import json
import os
from groq import Groq
from app.config import settings
from typing import Dict, Any

class HotelAgent:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.hotel_data = self.load_hotel_data()
    
    def load_hotel_data(self) -> Dict[str, Any]:
        """Load hotel information from JSON file"""
        try:
            with open('hotel_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to default if file missing
            return {
                "hotel_name": "Luxury Hotel",
                "city": "Accra, Ghana",
                "breakfast": {"hours": "6:30 AM - 10:30 AM", "location": "Main Restaurant"},
                "wifi": {"ssid": "HotelWiFi", "password": "ask front desk"},
                "check_in": "2:00 PM",
                "check_out": "12:00 PM"
            }
    
    async def process_message(self, message: str, hotel_context: Dict[str, Any], guest_name: str = "Guest") -> Dict[str, Any]:
        """Process guest message using hotel data"""
        
        # Build a detailed prompt with hotel data
        hotel_name = self.hotel_data.get("hotel_name", "our hotel")
        city = self.hotel_data.get("city", "Accra")
        
        breakfast = self.hotel_data.get("breakfast", {})
        breakfast_info = f"{breakfast.get('hours', '6:30-10:30')} at {breakfast.get('location', 'the restaurant')}"
        
        wifi = self.hotel_data.get("wifi", {})
        wifi_info = f"SSID: {wifi.get('ssid', 'HotelWiFi')}, Password: {wifi.get('password', 'ask front desk')}"
        
        pool = self.hotel_data.get("pool", {})
        pool_info = f"{pool.get('hours', '7 AM - 9 PM')} at {pool.get('location', 'pool area')}"
        
        gym = self.hotel_data.get("gym", {})
        gym_info = f"{gym.get('hours', '24/7')} at {gym.get('location', 'basement')}"
        
        spa = self.hotel_data.get("spa", {})
        spa_info = f"{spa.get('name', 'Spa')} open {spa.get('hours', '9 AM - 8 PM')}, call {spa.get('booking', 'extension 123')}"
        
        restaurant = self.hotel_data.get("restaurant", {})
        restaurant_info = f"{restaurant.get('name', 'Restaurant')} open {restaurant.get('hours', '12-10:30 PM')}, cuisine: {restaurant.get('cuisine', 'local & international')}"
        
        # Build local recommendations string
        local_recs = self.hotel_data.get("local_recommendations", [])
        recs_text = ""
        for rec in local_recs[:3]:  # Limit to top 3
            recs_text += f"- {rec['name']} ({rec['distance']}): {rec.get('cuisine', rec.get('type', 'recommended'))}\n"
        
        policies = self.hotel_data.get("policies", {})
        policy_text = f"Cancellation: {policies.get('cancellation', '24-hour policy')}, Children: {policies.get('children', 'contact hotel')}"
        
        prompt = f"""You are the AI concierge for {hotel_name} in {city}, Ghana.

HOTEL DETAILS:
- Check-in: {self.hotel_data.get('check_in', '2:00 PM')}
- Check-out: {self.hotel_data.get('check_out', '12:00 PM')}
- Breakfast: {breakfast_info}
- WiFi: {wifi_info}
- Pool: {pool_info}
- Gym: {gym_info}
- Spa: {spa_info}
- Restaurant: {restaurant_info}
- Policies: {policy_text}

LOCAL RECOMMENDATIONS:
{recs_text}

GUEST: {guest_name}
GUEST QUESTION: "{message}"

Respond as a warm, professional Ghanaian concierge. Use "Sir" or "Madam" appropriately. Keep answers concise (2-3 sentences). Be specific with times, locations, and prices when relevant.

Your response:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=250
            )
            
            ai_response = response.choices[0].message.content
            
            # Simple intent detection (optional)
            intent = "general"
            msg_lower = message.lower()
            if "breakfast" in msg_lower:
                intent = "breakfast"
            elif "check-out" in msg_lower or "checkout" in msg_lower:
                intent = "check_out"
            elif "check-in" in msg_lower or "checkin" in msg_lower:
                intent = "check_in"
            elif "wifi" in msg_lower or "internet" in msg_lower:
                intent = "wifi"
            elif "pool" in msg_lower:
                intent = "pool"
            elif "spa" in msg_lower:
                intent = "spa"
            elif "restaurant" in msg_lower or "dinner" in msg_lower or "lunch" in msg_lower:
                intent = "restaurant"
            elif "recommend" in msg_lower or "nearby" in msg_lower:
                intent = "local_recommendation"
            
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
                "response": f"I apologize Sir/Madam, I'm having technical difficulties. Please call the front desk at extension 0. (Error: {str(e)[:50]})",
                "needs_human": True,
                "action_needed": "none"
            }