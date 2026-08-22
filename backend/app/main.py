from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import api_router
from app.config import get_settings
from app.core.logging import configure_logging, log
from app.core.rate_limit import limiter

settings = get_settings()
configure_logging(settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("app_startup", env=settings.ENV)
    yield
    log.info("app_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    description="מערכת מודיעין עסקי, מכרזים ולידים לתחום הריהוט בישראל",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "message": "קלט לא תקין"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
