from pymongo import MongoClient

from api_config import settings

client = MongoClient(settings.mongo_uri)
db = client[settings.db_name]
users_collection = db[settings.db_collection_name]
counters_collection = db[settings.counters_collection_name]
