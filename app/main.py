from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.connections import close_postgre, get_redis, close_redis, connect_db
from system_config import system_config
from app.routes import users, auth, companies, company_actions, quiz_routes, quiz_statistics, notifications
from app.tasks.tasks import scheduler

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(company_actions.router)
app.include_router(quiz_routes.router)
app.include_router(quiz_statistics.router)
app.include_router(notifications.router)


@app.on_event("startup")
async def startup():
    await connect_db()
    await get_redis()
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    await close_postgre()
    await close_redis()


@app.get('/')
async def health_check():
    return {
        "status_code": 200,
        "detail": "ok",
        "result": "working"
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=system_config.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=system_config.app_host,
        port=system_config.app_port,
        reload=system_config.debug
    )
