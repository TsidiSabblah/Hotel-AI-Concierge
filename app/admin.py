from sqladmin import Admin, ModelView
from app.db import (
    Hotel, Guest, Conversation, Message, HotelKnowledge, engine
)

# --- Model Views ---
class HotelAdmin(ModelView, model=Hotel):
    column_list = [Hotel.id, Hotel.name, Hotel.phone_number, Hotel.city, Hotel.created_at]
    column_searchable_list = [Hotel.name, Hotel.city]
    page_size = 20

class GuestAdmin(ModelView, model=Guest):
    column_list = [Guest.id, Guest.name, Guest.phone_number, Guest.room_number, Guest.is_checked_in]
    column_searchable_list = [Guest.name, Guest.phone_number]
    page_size = 20

class ConversationAdmin(ModelView, model=Conversation):
    column_list = [Conversation.id, Conversation.guest_id, Conversation.channel, Conversation.started_at]
    column_searchable_list = [Conversation.guest_id]
    page_size = 20

class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.conversation_id, Message.direction, Message.content, Message.created_at]
    page_size = 20

class HotelKnowledgeAdmin(ModelView, model=HotelKnowledge):
    column_list = [HotelKnowledge.id, HotelKnowledge.hotel_id, HotelKnowledge.category, HotelKnowledge.question]
    page_size = 20

# --- Function to attach admin to a FastAPI app ---
def setup_admin(app):
    admin = Admin(app, engine, title="Hotel AI Concierge Admin")
    admin.add_view(HotelAdmin)
    admin.add_view(GuestAdmin)
    admin.add_view(ConversationAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(HotelKnowledgeAdmin)
    return admin