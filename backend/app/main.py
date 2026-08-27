import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import auth, executions, health, schedules, tests
from app.scheduler import scheduler_manager
from app.services.execution_service import trigger_scheduled_execution

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_scheduler")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager handling startup & shutdown lifecycle."""
    logger.info("Initializing database tables if not present...")
    init_db()
    logger.info("Initializing APScheduler background service on startup...")
    scheduler_manager.start()
    scheduler_manager.load_active_schedules_on_startup(
        db_factory=SessionLocal,
        job_func=trigger_scheduled_execution,
    )
    yield

    logger.info("Stopping APScheduler background service on shutdown...")
    scheduler_manager.shutdown(wait=False)


# Instantiate FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-stack Automated Test Execution Scheduler REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(tests.router, prefix=settings.API_PREFIX)
app.include_router(executions.router, prefix=settings.API_PREFIX)
app.include_router(schedules.router, prefix=settings.API_PREFIX)






# Application-level global error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Unhandled exception handler providing standardized error format."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": str(exc) if settings.DEBUG else "Internal Server Error",
        },
    )


@app.get("/", include_in_schema=False)
def root_redirect():
    """Root endpoint info response."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }
