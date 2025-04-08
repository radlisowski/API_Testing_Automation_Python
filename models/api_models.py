""" Every class in this file is built on Pydantic's BaseModel, which automatically checks and organizes data.
This setup makes sure that the information fits expected formats and gives clear feedback if something isn't right.
Declared once can be reused throughout the framework"""

from typing import List, Optional  # Import List for typing collections and Optional for nullable fields
from pydantic import BaseModel, Field  # Import BaseModel and Field from Pydantic for data validation and model creation


# Define a model for PhoneNumber using Pydantic
class PhoneNumber(BaseModel):
    type: str  # Represents the type of phone number, e.g., 'home' or 'work'
    number: str  # The phone number itself as a string


# Define a model for Address using Pydantic
class Address(BaseModel):
    street: str  # The street name and number
    city: str  # The city of the address
    country: str  # The country of the address
    phone_numbers: List[PhoneNumber]  # A list to hold multiple PhoneNumbers associated with the address


# Define a model for User using Pydantic
class User(BaseModel):
    """
    The User model defines both required and optional fields for a user.
    To designate a field as mandatory, we use the 'Field' function with the Ellipsis ('...')
    as a placeholder. This is applied to the 'username' and 'email' fields, ensuring these must
    be provided whenever an instance of the User model is created. Optional fields, like 'user_id',
    are marked with 'Optional', allowing flexibility by being either set or unset.
    """
    username: str = Field(..., description="The username of the user")  # Mandatory username field with description
    role: str = Field(..., description="The role of the user")  # Mandatory role field with description
    email: str = Field(..., description="The email of the user")  # Mandatory and Unique email field with description
    addresses: List[Address]  # A list of Address instances associated with the user
    user_id: Optional[int] = None  # An optional user ID that can be either an integer or None
