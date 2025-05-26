from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, clients, orders, products

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(clients.router, prefix="/clients")
app.include_router(orders.router, prefix="/orders")
app.include_router(products.router, prefix="/products")


@app.get("/")
def root():
    return {"message": "Welcome to the Lu Estilo api."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
