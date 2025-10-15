from typing import Any, Dict, Optional

import httpx


class N8NClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> Dict[str, str]:
        # n8n supports API key via X-N8N-API-KEY
        return {"X-N8N-API-KEY": self.api_key, "Content-Type": "application/json"}

    async def list_workflows(self) -> Any:
        resp = await self._client.get(f"{self.base_url}/workflows", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def create_workflow(self, workflow: Dict[str, Any]) -> Any:
        payload = {"name": workflow.get("name", "New Workflow"), "active": workflow.get("active", False), "nodes": workflow["nodes"], "connections": workflow["connections"]}
        resp = await self._client.post(f"{self.base_url}/workflows", headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Any:
        resp = await self._client.patch(f"{self.base_url}/workflows/{workflow_id}", headers=self._headers(), json=updates)
        resp.raise_for_status()
        return resp.json()

    async def delete_workflow(self, workflow_id: str) -> Any:
        resp = await self._client.delete(f"{self.base_url}/workflows/{workflow_id}", headers=self._headers())
        resp.raise_for_status()
        return {"deleted": True, "id": workflow_id}

    async def run_workflow(self, workflow_id: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        body = {"workflowId": workflow_id}
        if payload:
            body.update(payload)
        resp = await self._client.post(f"{self.base_url}/workflows/run", headers=self._headers(), json=body)
        resp.raise_for_status()
        return resp.json()

    async def get_execution_status(self, execution_id: str) -> Any:
        resp = await self._client.get(f"{self.base_url}/executions/{execution_id}", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()