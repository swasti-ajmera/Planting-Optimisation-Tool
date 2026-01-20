from fastapi import FastAPI
from .routers import auth, user, species, farm, recommendation, soil_texture, environmental_profile
from .database import engine, Base

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(species.router)
app.include_router(farm.router)
app.include_router(recommendation.router)
app.include_router(soil_texture.router)
app.include_router(environmental_profile.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Planting Optimisation Tool API"}
