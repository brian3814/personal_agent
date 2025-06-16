import uvicorn
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from .router.hello import router as hello_router

app = FastAPI()
app.include_router(hello_router)
mcp = FastApiMCP(app, name="personalAgent", description="Personal Agent")
mcp.mount()

@app.get("/")
def greeting():
    return {"message": "Hello, Agent!"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)

if __name__ == "__main__":
    main()