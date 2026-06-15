from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    agent_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    business_id: str
    email: str

class UserOut(BaseModel):
    email: str
    business_id: str

