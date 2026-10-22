import logging
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from agent.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous AI Agent",
    description="An autonomous agent that plans, executes, reflects, and generates Word documents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    request: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Natural language request for the agent",
        examples=["Create a Q4 marketing strategy for a B2B SaaS startup"],
    )


class TaskItem(BaseModel):
    id: int
    title: str
    status: str


class ExecutionResultItem(BaseModel):
    task_id: int
    task_title: str
    section_heading: str
    content_length: int
    revised: bool


class ReflectionSummary(BaseModel):
    overall_quality: str | None
    score: int | None
    feedback: str | None
    assumptions_made: list[str]


class DocumentInfo(BaseModel):
    filename: str
    base64: str


class AgentResponse(BaseModel):
    status: str
    request: str
    plan: dict
    task_list: list[TaskItem]
    execution_results: list[ExecutionResultItem]
    reflection: ReflectionSummary
    document: DocumentInfo
    execution_log: list[dict]


@app.get("/")
def root():
    return {
        "service": "Autonomous AI Agent",
        "version": "1.0.0",
        "endpoints": {
            "POST /agent": "Submit a request for the agent to process",
            "GET /health": "Health check",
        },
        "engineering_improvement": "Multi-step planning with Reflection/Self-check",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/agent", response_model=AgentResponse)
def run_agent(req: AgentRequest):
    logger.info(f"Received agent request: {req.request[:100]}...")

    orchestrator = AgentOrchestrator()
    try:
        result = orchestrator.run(req.request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Planning/validation error: {e}")
    except Exception as e:
        logger.error(f"Agent error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")

    logger.info(f"Agent completed: {result['document']['filename']}")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
