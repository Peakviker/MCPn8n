"""FastAPI MCP-compatible server bridging requests to the n8n REST API."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, BaseSettings, Field, HttpUrl
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("mcp_server")
logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    n8n_base_url: HttpUrl = Field(
        default="http://localhost:5678/api/v1/",
        description="Base URL for the n8n REST API.",
        env=["N8N_URL", "N8N_BASE_URL"],
    )
    n8n_api_key: Optional[str] = Field(
        default=None,
        description="API key for authenticating against n8n.",
        env=["N8N_API_KEY", "N8N_API_TOKEN"],
    )
    n8n_timeout: float = Field(default=30.0, description="HTTP timeout in seconds.")

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


class ListWorkflowsParams(BaseModel):
    limit: Optional[int] = Field(default=None, ge=1, description="Maximum number of workflows to fetch.")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for pagination.")


class CreateWorkflowParams(BaseModel):
    workflow: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload describing the workflow to create (as accepted by n8n).",
    )


class UpdateWorkflowParams(BaseModel):
    workflow_id: str = Field(..., description="Identifier of the workflow to update.")
    workflow: Dict[str, Any] = Field(
        default_factory=dict,
        description="Updated workflow payload compatible with the n8n API.",
    )


class DeleteWorkflowParams(BaseModel):
    workflow_id: str = Field(..., description="Identifier of the workflow to delete.")


class RunWorkflowParams(BaseModel):
    workflow_id: Optional[str] = Field(
        default=None,
        description="Identifier of the workflow to execute. When omitted, payload must contain workflow data.",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution parameters forwarded to n8n (for example runData/startNodes).",
    )


class GetExecutionStatusParams(BaseModel):
    execution_id: str = Field(..., description="Execution identifier returned by n8n.")


class MCPRequest(BaseModel):
    id: str = Field(..., description="Request identifier provided by the MCP client.")
    method: str = Field(
        ...,
        description="MCP method name, such as list_workflows or create_workflow.",
    )
    params: Dict[str, Any] = Field(default_factory=dict, description="Method-specific parameters.")


class MCPError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[MCPError] = None


class N8nClient:
    """Lightweight async wrapper around the n8n REST API."""

    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client

    async def list_workflows(self, params: ListWorkflowsParams) -> Dict[str, Any]:
        logger.debug("Listing workflows with params=%s", params.dict())
        response = await self._client.get(
            "rest/workflows", params=params.dict(exclude_none=True) or None
        )
        response.raise_for_status()
        return response.json()

    async def create_workflow(self, params: CreateWorkflowParams) -> Dict[str, Any]:
        logger.debug("Creating workflow with payload keys=%s", list(params.workflow.keys()))
        response = await self._client.post("rest/workflows", json=params.workflow)
        response.raise_for_status()
        return response.json()

    async def update_workflow(self, params: UpdateWorkflowParams) -> Dict[str, Any]:
        logger.debug("Updating workflow %s", params.workflow_id)
        response = await self._client.patch(
            f"rest/workflows/{params.workflow_id}", json=params.workflow
        )
        response.raise_for_status()
        return response.json()

    async def delete_workflow(self, params: DeleteWorkflowParams) -> Dict[str, Any]:
        logger.debug("Deleting workflow %s", params.workflow_id)
        response = await self._client.delete(f"rest/workflows/{params.workflow_id}")
        response.raise_for_status()
        return response.json() if response.content else {"status": "deleted"}

    async def run_workflow(self, params: RunWorkflowParams) -> Dict[str, Any]:
        logger.debug("Running workflow %s", params.workflow_id)
        payload = dict(params.payload)
        if params.workflow_id:
            payload.setdefault("workflowId", params.workflow_id)
        response = await self._client.post("rest/workflows/run", json=payload or None)
        response.raise_for_status()
        return response.json()

    async def get_execution_status(self, params: GetExecutionStatusParams) -> Dict[str, Any]:
        logger.debug("Fetching execution status for %s", params.execution_id)
        response = await self._client.get(f"rest/executions/{params.execution_id}")
        response.raise_for_status()
        return response.json()


async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    headers = {}
    if settings.n8n_api_key:
        headers["X-N8N-API-KEY"] = settings.n8n_api_key

    client = httpx.AsyncClient(
        base_url=str(settings.n8n_base_url),
        headers=headers,
        timeout=settings.n8n_timeout,
    )
    app.state.n8n_client = N8nClient(client)
    logger.info("Initialised n8n client with base URL %s", settings.n8n_base_url)
    try:
        yield
    finally:
        await client.aclose()
        logger.info("n8n client closed")


app = FastAPI(title="MCP n8n bridge", lifespan=lifespan)


def get_n8n_client() -> N8nClient:
    return app.state.n8n_client  # type: ignore[attr-defined]


@app.get("/mcp/discover")
async def discover() -> JSONResponse:
    """Return MCP capability description."""
    payload = {
        "name": "n8n MCP bridge",
        "version": "1.0.0",
        "capabilities": {
            "sse": True,
            "methods": [
                "list_workflows",
                "create_workflow",
                "update_workflow",
                "delete_workflow",
                "run_workflow",
                "get_execution_status",
            ],
        },
    }
    logger.info("Discovery requested: %s", payload)
    return JSONResponse(payload)


METHOD_PARAM_MODELS: Dict[str, Callable[[Dict[str, Any]], BaseModel]] = {
    "list_workflows": ListWorkflowsParams.parse_obj,
    "create_workflow": CreateWorkflowParams.parse_obj,
    "update_workflow": UpdateWorkflowParams.parse_obj,
    "delete_workflow": DeleteWorkflowParams.parse_obj,
    "run_workflow": RunWorkflowParams.parse_obj,
    "get_execution_status": GetExecutionStatusParams.parse_obj,
}


async def dispatch_request(request: MCPRequest, client: N8nClient) -> Dict[str, Any]:
    if request.method not in METHOD_PARAM_MODELS:
        logger.error("Unsupported MCP method: %s", request.method)
        raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")

    parser = METHOD_PARAM_MODELS[request.method]
    params_model = parser(request.params)
    handler = getattr(client, request.method)
    logger.info("Dispatching method=%s id=%s", request.method, request.id)
    return await handler(params_model)


@app.post("/mcp/request")
async def handle_mcp_request(request: MCPRequest, client: N8nClient = Depends(get_n8n_client)) -> EventSourceResponse:
    logger.info("Received MCP request id=%s method=%s", request.id, request.method)

    async def event_publisher() -> AsyncIterator[Dict[str, str]]:
        try:
            result = await dispatch_request(request, client)
            response = MCPResponse(
                id=request.id,
                result={
                    "type": "json_schema",
                    "data": result,
                },
            )
            logger.info("MCP request id=%s succeeded", request.id)
            yield {
                "event": "result",
                "data": response.json(),
            }
        except httpx.HTTPStatusError as exc:
            error = MCPError(
                code=str(exc.response.status_code),
                message="n8n API returned an error",
                details={
                    "response": exc.response.json() if exc.response.content else None,
                },
            )
            logger.exception("n8n API error for request id=%s", request.id)
            yield {
                "event": "error",
                "data": MCPResponse(id=request.id, error=error).json(),
            }
        except httpx.HTTPError as exc:
            error = MCPError(code="http_error", message=str(exc))
            logger.exception("HTTP error for request id=%s", request.id)
            yield {
                "event": "error",
                "data": MCPResponse(id=request.id, error=error).json(),
            }
        except Exception as exc:  # pragma: no cover - catch-all for robustness
            error = MCPError(code="internal_error", message=str(exc))
            logger.exception("Internal error for request id=%s", request.id)
            yield {
                "event": "error",
                "data": MCPResponse(id=request.id, error=error).json(),
            }

    return EventSourceResponse(event_publisher())


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
