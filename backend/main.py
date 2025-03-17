from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from invoice_routes import router as invoice_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# JWT Config
SECRET_KEY = "169999f8d0064cdda164107d96ccfb98ba2196691777483f7ca252449d05935f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI instance
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(invoice_router)

# OAuth2 scheme (for login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# HTTPBearer scheme (for Swagger UI token input)
bearer_scheme = HTTPBearer()

# User and Token models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# JWT token creation
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Login endpoint (get token)
@app.post("/token", response_model=Token)
def login_for_access_token(user: User):
    if user.username == "test" and user.password == "test123":
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Token verification function
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalid")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

# Example protected endpoint
@app.get("/users/me")
def read_users_me(username: str = Depends(verify_token)):
    return {"username": username}

# Custom Swagger UI to enable BearerAuth on protected endpoints
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Invoice API",
        version="1.0.0",
        description="API for invoice upload and user authentication with JWT",
        routes=app.routes,
    )

    # Define BearerAuth scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply BearerAuth only to protected endpoints (skip /token)
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if path != "/token":
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set custom OpenAPI schema
app.openapi = custom_openapi
