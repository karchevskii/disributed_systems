import datetime
import re
import string
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

class UserAddSchema(BaseModel):
    username: str = Field(..., example="John", description="Name")
    surname: str = Field(..., example="Doe", description="Surname")
