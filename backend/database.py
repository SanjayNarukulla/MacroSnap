import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
db = client["macrosnap"]

users_col = db["users"]
sessions_col = db["sessions"]
messages_col = db["messages"]
