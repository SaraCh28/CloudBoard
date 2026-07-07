import asyncio
from httpx import AsyncClient

async def test():
    async with AsyncClient(base_url="http://localhost:8000/api/v1") as ac:
        # Create a task
        res = await ac.post("/tasks", json={
            "id": "PHX-999",
            "title": "Test Task",
            "description": "Just testing the API",
            "status": "Todo",
            "priority": "High"
        })
        print("POST", res.status_code, res.json())
        
        # Get tasks
        res = await ac.get("/tasks")
        print("GET", res.status_code, res.json())

asyncio.run(test())
