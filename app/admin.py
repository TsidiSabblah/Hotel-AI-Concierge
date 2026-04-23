from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.db import (
    Hotel, Guest, Conversation, Message, HotelKnowledge, engine
)
import os

# ---------- Authentication ----------
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        # Read credentials from environment variables
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        if username == admin_user and password == admin_pass:
            request.session.update({"is_admin": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("is_admin", False)

# ---------- Model Views ----------
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

# ---------- Admin Setup ----------
def setup_admin(app):
    secret_key = os.getenv("ADMIN_SECRET_KEY", "your-super-secret-key-change-in-production")
    authentication_backend = AdminAuth(secret_key=secret_key)
    admin = Admin(
        app,
        engine,
        title="Hotel AI Concierge Admin",
        authentication_backend=authentication_backend
    )
    admin.add_view(HotelAdmin)
    admin.add_view(GuestAdmin)
    admin.add_view(ConversationAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(HotelKnowledgeAdmin)
    print("✅ Admin panel mounted at /admin (authentication enabled)")