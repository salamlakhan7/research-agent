from pydantic import BaseModel


class ResearchRequest(BaseModel):
    mode: str = "topic"        # "topic" or "links"
    input: str
    length: str = "short"      # tldr / short / detailed
    style: str = "bullets"     # bullets / executive / eli5

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class NameRequest(BaseModel):
    name: str


class PasswordRequest(BaseModel):
    current: str
    new: str


class DeleteRequest(BaseModel):
    password: str


class RelatedRequest(BaseModel):
    text: str