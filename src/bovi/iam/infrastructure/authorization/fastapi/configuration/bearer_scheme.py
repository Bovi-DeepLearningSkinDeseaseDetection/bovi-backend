from fastapi.security import HTTPBearer

# auto_error=False: a missing token becomes our own 401 in Spanish instead of FastAPI's.
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="JWT",
    description="Access token de /api/v1/auth/login (Authorization: Bearer <token>)",
)
