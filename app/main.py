from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.main import api_router
from app.core.config import settings
from app.db.session import engine
from sqlmodel import SQLModel

# Define the lifespan function
def lifespan(app: FastAPI):
    # Code executed on startup
    SQLModel.metadata.create_all(bind=engine)
    yield  # App runs here
app = FastAPI(
    root_path="/api",
    lifespan=lifespan,
    title="Joyful api",
    description="Joyful api application.",
    version="1.0.0",
    docs_url="/docs",  # Change Swagger UI path
    redoc_url="/redoc",  # Change ReDoc path
    )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Banner Images
app.mount("/images", StaticFiles(directory="."), name="images")  # Serves banners under /static/
