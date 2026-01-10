from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.session import router as session_router
from app.api.dialog import router as dialog_router
from app.api.tools import router as tools_router

load_dotenv()
app = FastAPI(title="Community Agent API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(session_router)
app.include_router(dialog_router)
app.include_router(tools_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
