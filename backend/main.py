from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers import auth_router, chat_router, products_router, saved_router

app = FastAPI(title="Product Review Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(saved_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "Product Review Chat API", "version": "2.0.0", "database": "Supabase"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
