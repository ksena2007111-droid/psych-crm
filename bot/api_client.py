import httpx

BASE_URL = "http://127.0.0.1:8000/api"


async def get_services(psychologist_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/public/psychologist/{psychologist_id}/services")
        return r.json() if r.status_code == 200 else []


async def get_slots(psychologist_id: int, date: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/public/psychologist/{psychologist_id}/slots", params={"date": date})
        return r.json() if r.status_code == 200 else {"slots": []}


async def register_client(telegram_id: int, name: str, phone: str = None, email: str = None):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/public/clients/register", json={
            "telegram_id": telegram_id,
            "name": name,
            "phone": phone,
            "email": email,
        })
        return r.json() if r.status_code == 200 else None


async def get_client_by_telegram(telegram_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/public/clients/{telegram_id}")
        if r.status_code == 404:
            return None
        return r.json() if r.status_code == 200 else None

async def check_client_exists(telegram_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/public/clients/{telegram_id}")
        return r.status_code == 200

async def create_booking(telegram_id: int, psychologist_id: int, service_id: int, date: str, time: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/public/bookings", json={
            "telegram_id": telegram_id,
            "psychologist_id": psychologist_id,
            "service_id": service_id,
            "date": date,
            "time": time,
        })
        return r.json() if r.status_code == 200 else None


async def get_client_bookings(telegram_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/public/clients/{telegram_id}/bookings")
        return r.json() if r.status_code == 200 else []


async def cancel_booking(booking_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.patch(f"{BASE_URL}/public/bookings/{booking_id}/cancel")
        return r.status_code == 200