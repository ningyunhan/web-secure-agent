from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from core.rag_engine import RAGEngine
from core.fingerprint_engine import FingerprintEngine
from core.knowledge_manager import KnowledgeManager
from api import recognize, batch_test, knowledge
from utils.logger import logger
from config import config

app = FastAPI(title="资产指纹识别系统", version="1.0.0")

# 跨域配置（允许前端本地开发访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化核心组件（全局单例）
logger.info("="*60)
logger.info("资产指纹识别系统启动中...")
logger.info("LLM Provider: %s | Model: %s | Base URL: %s",
           config.LLM_PROVIDER, config.LLM_MODEL, config.OPENAI_BASE_URL)
logger.info("ChromaDB Path: %s | RAG Top-K: %d", config.CHROMA_DB_PATH, config.RAG_TOP_K)

rag = RAGEngine()
logger.info("RAGEngine 初始化完成，向量库条目数: %d", rag.get_all_count())

km = KnowledgeManager(rag)
km.init_from_json()
logger.info("KnowledgeManager 初始化完成，JSON 知识条目数: %d", len(km.list_all()))

engine = FingerprintEngine(rag)
logger.info("FingerprintEngine 初始化完成")

# 注入到路由模块
recognize.set_engine(engine)
batch_test.set_engine(engine)
knowledge.set_km(km)
logger.info("路由依赖注入完成")

# 注册路由
app.include_router(recognize.router, prefix="/api", tags=["指纹识别"])
app.include_router(batch_test.router, prefix="/api", tags=["批量测试"])
app.include_router(knowledge.router, prefix="/api", tags=["知识库管理"])

logger.info("路由注册完成: POST /api/recognize, GET /api/batch-test/run, CRUD /api/knowledge")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """HTTP 请求日志中间件"""
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    # 跳过健康检查的详细日志（只记录 INFO）
    if request.url.path == "/":
        logger.debug("%s %s -> %d (%.0fms)", request.method, request.url.path,
                     response.status_code, duration_ms)
    else:
        logger.info("%s %s -> %d (%.0fms)", request.method, request.url.path,
                    response.status_code, duration_ms)
    return response


@app.get("/")
def health_check():
    """健康检查"""
    return {"status": "ok", "knowledge_count": rag.get_all_count()}


@app.on_event("shutdown")
def shutdown_event():
    logger.info("资产指纹识别系统关闭")
