from pydantic import BaseModel, Field


class Review(BaseModel):
    review_id: str
    content: str
    rating: float | None = None
    date: str | None = None


class Product(BaseModel):
    product_id: str
    name: str
    description: str
    image: str | None = None
    reviews: list[Review] = []


class ChatMessage(BaseModel):
    product_id: str
    message: str
    conversation_history: list[dict] | None = []


class ProductUpload(BaseModel):
    product_id: str
    name: str
    description: str
    image: str | None = None
    reviews: list[Review]


class AuthSignUp(BaseModel):
    name: str
    username: str
    password: str = Field(min_length=6)


class AuthSignIn(BaseModel):
    username: str
    password: str = Field(min_length=6)


class SavedProductPayload(BaseModel):
    product_id: str
    interest_level: str
    personal_note: str | None = ""
