from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=4, max_length=128)


class PlayerRead(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
