#!/usr/bin/env python3

from fastapi import FastAPI
from projects.api import router as projects_router

app = FastAPI()
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])

if __name__ == "__main__":
    import uvicorn
    print("Starting test server...")
    print("Routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    
    uvicorn.run(app, host="0.0.0.0", port=8001) 