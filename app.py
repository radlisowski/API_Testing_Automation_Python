from fastapi import FastAPI

app = FastAPI()


@app.get("/users/")
async def root():
    return {"message": "Hello World"}
