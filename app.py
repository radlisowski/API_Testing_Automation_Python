import os

import uvicorn  # Uvicorn is an ASGI server for running asynchronous web applications
from fastapi import FastAPI, HTTPException, Request, status  # FastAPI framework imports to handle requests and exceptions
from pymongo import MongoClient  # MongoDB client to interact with the database
from models.api_models import *  # Import Pydantic models for data validation

# Initialize a new FastAPI application
app = FastAPI()

# Connect to a MongoDB instance
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_db_name = os.getenv("MONGO_DB_NAME", "UserDatabase")
client = MongoClient(mongo_uri)  # Connects to MongoDB
db = client[mongo_db_name]  # Selects the database to work with
users_collection = db["UserCollection"]  # Stores user documents
counters_collection = db["Counters"]  # Stores auto-increment counters


def get_next_sequence(name: str) -> int:
    """
    Atomically increment a counter document to provide unique user IDs.
    `find_one_and_update` is used to ensure that each user_id is unique and incremented safely.
    """
    result = counters_collection.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, return_document=True, upsert=True
    )
    return result["seq"]  # Returns the updated sequence number


@app.get("/user/{user_id}", response_model=User, status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    """
    Retrieve a user by user_id from the database.
    If the user is not found, raises a 404 HTTPException.
    """
    user_doc = users_collection.find_one({"user_id": user_id})  # Fetch the user document using user_id
    if user_doc is None:
        raise HTTPException(status_code=404, detail="User not found")  # User ID does not exist in the database

    user = User(**user_doc)  # Convert the database record to a Pydantic User model
    return user  # Return the user model as a response


@app.post("/user/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    """
    Create a new user in the database.
    Validates that mandatory fields are present and that the email address is unique, then inserts the user document.
    """
    user_id = get_next_sequence("user_id")  # Generate a unique ID for the new user
    user.user_id = user_id  # Assign this ID to the user object

    # Validate that 'username' and 'email' are indeed provided
    if not user.username or not user.email:
        missing_field = 'username' if not user.username else 'email'
        raise HTTPException(status_code=400, detail=f"{missing_field.capitalize()} is required.")  # Missing field

    # Check if the email is unique
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=400,
            detail=f"User Email {user.email} already exists."
        )

    user_dict = user.model_dump()  # Convert the Pydantic model to a dictionary

    # Insert the new user document into MongoDB
    users_collection.insert_one(user_dict)

    return user  # Return the created user model as the response


@app.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    """
    Delete a user by user_id from the database.
    If the user is not found, raises a 404 HTTPException.
    """
    result = users_collection.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted successfully"}


# Run the application with Uvicorn if this script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5556)  # Launch the app on port 5556
