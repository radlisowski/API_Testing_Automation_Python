from pymongo.collection import Collection

from api.database import counters_collection, users_collection
from models.api_models import User


class UserRepository:
    def __init__(self, user_collection: Collection, counter_collection: Collection):
        self.user_collection = user_collection
        self.counter_collection = counter_collection

    def get_next_sequence(self, name: str) -> int:
        result = self.counter_collection.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            return_document=True,
            upsert=True,
        )
        return result["seq"]

    def find_by_user_id(self, user_id: int) -> dict | None:
        return self.user_collection.find_one({"user_id": user_id})

    def find_by_email(self, email: str) -> dict | None:
        return self.user_collection.find_one({"email": email})

    def insert_user(self, user: User) -> None:
        self.user_collection.insert_one(user.model_dump(mode="json"))

    def delete_by_user_id(self, user_id: int) -> bool:
        result = self.user_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0


user_repository = UserRepository(users_collection, counters_collection)
