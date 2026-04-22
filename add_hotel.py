import asyncio
from app.db import create_hotel
from app.config import settings

async def main():
    hotel_data = {
        "name": "Test Luxury Hotel Accra",
        "phone_number": "233123456789",
        "email": "reservations@testhotel.com",
        "address": "123 Independence Avenue, Accra, Ghana",
        "city": "Accra"
    }
    
    hotel = await create_hotel(hotel_data)
    print(f"✅ Hotel created!")
    print(f"   ID: {hotel.id}")
    print(f"   Name: {hotel.name}")
    print(f"   Phone: {hotel.phone_number}")

if __name__ == "__main__":
    asyncio.run(main())