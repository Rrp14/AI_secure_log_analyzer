from dotenv import load_dotenv
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "log_analyzer")

print("Connecting to Mongo...")

client = MongoClient(MONGO_URI)

try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully")
except Exception as e:
    print("MongoDB Connection Failed:", e)

db = client[DB_NAME]
incident_collection = db["incidents"]
log_collection=db["logs"]