from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=15,
        description="username: 3-15 chars",
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=72,
    )

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)