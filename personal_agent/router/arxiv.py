from fastapi import APIRouter

router = APIRouter()

@router.get("/arxiv")
def get_arxiv():
    return {"message": "Hello, World!"}