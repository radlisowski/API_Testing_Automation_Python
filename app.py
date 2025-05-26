import uvicorn  # Uvicorn is an ASGI server for running asynchronous web applications
from fastapi import FastAPI, HTTPException, Request, status  # FastAPI framework imports to handle requests and exceptions
from pymongo import MongoClient  # MongoDB client to interact with the database
from models.api_models import *  # Import Pydantic models for data validation


# Initialize a new FastAPI application
app = FastAPI()

# Connect to a MongoDB instance
client = MongoClient("mongodb://localhost:27017/")  # Connects to MongoDB on the default port
db = client["UserDatabase"]  # Selects the database to work with
collection = db["UserCollection"]  # Selects the collection that stores user documents


def get_next_sequence(name: str) -> int:
    """
    Atomically increment a counter document in the collection to provide unique user IDs.
    `find_one_and_update` is used to ensure that each user_id is unique and incremented safely.
    """
    result = collection.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, return_document=True, upsert=True
    )
    return result["seq"]  # Returns the updated sequence number


@app.get("/user/{user_id}", response_model=User, status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    """
    Retrieve a user by user_id from the database.
    If the user is not found, raises a 404 HTTPException.
    """
    user_doc = collection.find_one({"user_id": user_id})  # Fetch the user document using user_id
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
    if collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=400,
            detail=f"User Email {user.email} already exists."
        )

    user_dict = user.model_dump()  # Convert the Pydantic model to a dictionary

    # Insert the new user document into MongoDB
    collection.insert_one(user_dict)

    return user  # Return the created user model as the response

# Run the application with Uvicorn if this script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5556)  # Launch the app on port 5556
