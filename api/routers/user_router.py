from fastapi import APIRouter, status

from api.services.user_service import UserService, user_service
from models.api_models import User

router = APIRouter()


def get_user_service() -> UserService:
    return user_service


@router.get("/user/{user_id}", response_model=User, status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    return get_user_service().get_user(user_id)


@router.post("/user/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    return get_user_service().create_user(user)


@router.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    return get_user_service().delete_user(user_id)
