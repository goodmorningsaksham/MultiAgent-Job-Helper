from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.api.v1.companies import router as companies_router
from app.api.v1.templates import router as templates_router
from app.api.v1.chat import router as chat_router
from app.api.v1.insights import router as insights_router
from app.api.v1.streaming import router as streaming_router

settings = get_settings()

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = structlog.get_logger()
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc) if settings.debug else "Something went wrong"},
    )


app.include_router(companies_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(streaming_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name, "version": "1.0.0"}


@app.on_event("startup")
async def startup():
    structlog.get_logger().info("application_startup", debug=settings.debug)


@app.on_event("shutdown")
async def shutdown():
    from app.core.database import engine
    await engine.dispose()
