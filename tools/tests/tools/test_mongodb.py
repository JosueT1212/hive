import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGODB_URI")

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("¡Success!")
except Exception as e:
    print(e)
