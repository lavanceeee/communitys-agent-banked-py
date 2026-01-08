#fastAPI启动文件
#文档地址：http://127.0.0.1:8081/docs
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 配置全局参数
app = FastAPI(
    title="FastAPI 标准项目",
    description="包含跨域、异常处理的标准启动文件",
    version="1.0.0",
    docs_url="/docs",  # 自定义 Swagger 文档路径
    redoc_url="/redoc"  # 自定义 ReDoc 文档路径
)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/")
async def root():
    
    return {"message": "FastAPI 标准启动文件", "docs": "http://127.0.0.1:8081/docs"}



# 4. 启动入口
if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="localhost", 
        port=8081,
        reload=True,  
        workers=1  
    )