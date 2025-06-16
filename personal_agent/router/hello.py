from fastapi import APIRouter

router = APIRouter(prefix="/agent")

@router.get("/hello")
def say_hello():
    return {"message": "Hello, World!"}