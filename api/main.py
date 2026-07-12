from fastapi import FastAPI
from api.routes import posts, users, accounts, auth
from api.routes import oauth  

app = FastAPI(title="Virelo AI", version="1.0.0")

app.include_router(auth.router)
app.include_router(oauth.router)   
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(accounts.router)

@app.get("/")
def root():
    return {"message": "Virelo AI API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}