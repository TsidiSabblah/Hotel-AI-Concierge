from sqladmin import Admin, ModelView
from app.db import Hotel, Guest, Conversation, Message, HotelKnowledge, engine

# Define model views
class HotelAdmin(ModelView, model=Hotel):
    column_list = [Hotel.id, Hotel.name, Hotel.phone_number, Hotel.city]

class GuestAdmin(ModelView, model=Guest):
    column_list = [Guest.id, Guest.name, Guest.phone_number, Guest.room_number]

class ConversationAdmin(ModelView, model=Conversation):
    column_list = [Conversation.id, Conversation.guest_id, Conversation.channel, Conversation.started_at]

class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.conversation_id, Message.direction, Message.content]

class HotelKnowledgeAdmin(ModelView, model=HotelKnowledge):
    column_list = [HotelKnowledge.id, HotelKnowledge.hotel_id, HotelKnowledge.category, HotelKnowledge.question]

# This function will be called from main.py with the FastAPI app instance
def setup_admin(app):
    """Attach SQLAdmin to the FastAPI app."""
    admin = Admin(app, engine, title="Hotel AI Concierge Admin")
    admin.add_view(HotelAdmin)
    admin.add_view(GuestAdmin)
    admin.add_view(ConversationAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(HotelKnowledgeAdmin)
    print("✅ Admin panel mounted at /admin")