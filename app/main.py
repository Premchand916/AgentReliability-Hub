"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import Database
from app.routes import router


def create_app(database_url: str = "sqlite:///./agent_reliability.db") -> FastAPI:
    database = Database(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database.create_schema()
        yield
        app.state.database.dispose()

    app = FastAPI(title="AgentReliability Hub", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.include_router(router)

    @app.exception_handler(HTTPException)
    async def application_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        del request
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return app


app = create_app()
