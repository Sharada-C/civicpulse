from typing import Literal
from pydantic import BaseModel, EmailStr

Role = Literal["CITIZEN", "ANALYST", "ADMIN", "DEPARTMENT_OFFICER"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: Role = "CITIZEN"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
