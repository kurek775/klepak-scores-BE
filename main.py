from fastapi import FastAPI, APIRouter

app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url="/api/redoc")

api_router = APIRouter(prefix="/api")

# Define the routes under the "/api" prefix
@api_router.post("/tours/{tourId}/crews/{crewId}/upload-photo")
def upload_file(tourId: int, crewId: int):
    return {"message": f"Photo uploaded for tour {tourId} and crew {crewId}"}

@api_router.post("/tours/{tourId}/crews/{crewId}/sports/{sportId}/results")
def create_results(tourId: int, crewId: int,sportId: int):
    return {"message": "Results created"}

@api_router.get("/results")
def get_results():
    return {"data": "data"}

@api_router.put("/results")
def update_results():
    return {"data": "data"}

@api_router.get("/crews")
def get_crew():
    return {"data": "data"}

@api_router.get("/sports")
def get_sports():
    return {"data": "data"}

# Include the router in the main app
app.include_router(api_router)
