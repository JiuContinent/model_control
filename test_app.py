#!/usr/bin/env python3
"""
简单的测试应用
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Test App",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
