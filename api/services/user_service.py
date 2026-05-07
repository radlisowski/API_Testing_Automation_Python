from fastapi import HTTPException

from api.repositories.user_repository import UserRepository, user_repository
from models.api_models import User


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, user_id: int) -> User:
        user_doc = self.repository.find_by_user_id(user_id)
        if user_doc is None:
            raise HTTPException(status_code=404, detail="User not found")

        return User(**user_doc)

    def create_user(self, user: User) -> User:
        user_id = self.repository.get_next_sequence("user_id")
        user.user_id = user_id

        if not user.username or not user.email:
            missing_field = "username" if not user.username else "email"
            raise HTTPException(status_code=400, detail=f"{missing_field.capitalize()} is required.")

        if self.repository.find_by_email(str(user.email)):
            raise HTTPException(status_code=400, detail=f"User Email {user.email} already exists.")

        self.repository.insert_user(user)
        return user

    def delete_user(self, user_id: int) -> dict[str, str]:
        deleted = self.repository.delete_by_user_id(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": f"User {user_id} deleted successfully"}


user_service = UserService(user_repository)
