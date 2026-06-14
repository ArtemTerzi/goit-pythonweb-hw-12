from fastapi import FastAPI, APIRouter, Request
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api import contacts, utils, auth, users
from src.conf import messages

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": messages.REQUEST_LIMIT_EXCEEDED},
    )


api_router = APIRouter(prefix="/api")

api_router.include_router(utils.router)
api_router.include_router(contacts.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)

app.include_router(api_router)


def main():
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
