from pydantic import BaseModel, Field, model_validator, EmailStr

class UserRead(BaseModel):
    id: int = Field(gt=0)
    email: EmailStr
    username: str = Field(min_length=3)

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    password_confirmation: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match")

        return self
