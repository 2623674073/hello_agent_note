from pydantic import BaseModel

from fastapi import FastAPI


app = FastAPI()

@app.get("/tasks/{item}")
def task_search():
    return {}