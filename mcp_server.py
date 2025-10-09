import os
import json
import uuid
import time
import asyncio
import requests
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# ==========================================================
# Request/Response Models
# ==========================================================
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class RunRequest(BaseModel):
    model: Optional[str] = None
    endpoint_url: Optional[str] = None
    input: Dict[str, Any]
    output_type: str = "text"
    callback_url: Optional[str] = None


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


# ==========================================================
# MuApiClient
# ==========================================================
class MuApiClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.base_url = "https://api.muapi.ai/api/v1"

    def submit_task(self, endpoint_url: str, input_payload: Dict[str, Any]) -> str:
        """Submit a task and return the request_id"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        # Handle both full URLs and endpoint names
        if endpoint_url.startswith("http"):
            url = endpoint_url
        else:
            url = f"{self.base_url}/{endpoint_url}"
        
        response = requests.post(url, headers=headers, json=input_payload)
        
        if response.status_code not in [200, 201]:
            raise Exception(
                f"Error submitting task: {response.status_code}, {response.text}"
            )
        
        result = response.json()
        request_id = result.get("request_id")
        if not request_id:
            raise Exception(f"No request_id in response: {result}")
        
        return request_id

    def poll_result(self, request_id: str, max_polls: int = 300) -> Dict[str, Any]:
        """Poll for result until completion (with 150s timeout at 0.5s intervals)"""
        result_url = f"{self.base_url}/predictions/{request_id}/result"
        headers = {"x-api-key": self.api_key}
        
        polls = 0
        while polls < max_polls:
            response = requests.get(result_url, headers=headers)
            
            if response.status_code not in [200, 201]:
                raise Exception(
                    f"Error polling result: {response.status_code}, {response.text}"
                )
            
            result = response.json()
            status = result.get("status")
            
            if status == "completed":
                return result
            elif status == "failed":
                raise Exception(f"Task failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(0.5)
            polls += 1
        
        raise Exception(f"Task polling timeout after {max_polls * 0.5}s")

    def run_task(
        self,
        endpoint_url: str,
        input_payload: Dict[str, Any],
        output_type: str
    ) -> Dict[str, Any]:
        """Run a task synchronously"""
        request_id = self.submit_task(endpoint_url, input_payload)
        result = self.poll_result(request_id)
        
        outputs = result.get("outputs", [])
        return {
            "request_id": request_id,
            "status": result.get("status"),
            "outputs": [{"type": output_type, "url": url} for url in outputs],
            "created_at": result.get("created_at"),
            "timings": result.get("timings")
        }


# ==========================================================
# Model Parser
# ==========================================================
def parse_models(json_path: str) -> List[Dict[str, Any]]:
    """Parse models from JSON file"""
    if not os.path.exists(json_path):
        return []

    with open(json_path, "r") as f:
        raw_models = json.load(f)

    parsed = []
    for m in raw_models:
        try:
            input_schema = m.get("input_schema", {}).get("schemas", {}).get("input_data", {})
            
            props = input_schema.get("properties", {})
            schema_properties = {}
            
            for name, details in props.items():
                prop_def = {
                    "type": details.get("type", "string"),
                    "description": details.get("description", ""),
                }
                if details.get("enum"):
                    prop_def["enum"] = details.get("enum")
                if "default" in details:
                    prop_def["default"] = details.get("default")
                schema_properties[name] = prop_def

            parsed.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "description": m.get("description", ""),
                "endpoint_url": input_schema.get("endpoint_url", m.get("name")),
                "category": m.get("category", ""),
                "group_of": m.get("group_of", ""),
                "cost": m.get("cost", 0),
                "input_schema": {
                    "type": "object",
                    "properties": schema_properties,
                    "required": input_schema.get("required", [])
                },
                "output_type": "video" if m.get("group_of") == "video" else (
                    "text" if m.get("group_of") == "text" else "image"
                ),
            })
        except Exception as e:
            print(f"⚠️ Skipping model {m.get('name')}: {e}")
    
    return parsed


# ==========================================================
# FastAPI MCP Server
# ==========================================================
app = FastAPI(
    title="MuAPI MCP Server for Cursor",
    version="2.0",
    description="MCP-compliant server for text, image, and video generation"
)

# CORS middleware for Cursor integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS: List[Dict[str, Any]] = []
TASKS: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
def on_startup():
    """Load models on startup"""
    global MODELS
    models_path = os.getenv("MODELS_JSON", "models.json")
    MODELS = parse_models(models_path)
    print(f"✅ Loaded {len(MODELS)} models")
    for model in MODELS:
        print(f"  - {model['name']} ({model['category']})")


# ==========================================================
# Health & Status Endpoints
# ==========================================================
@app.get("/")
async def root():
    """Root endpoint with documentation"""
    return {
        "service": "MuAPI MCP Server",
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "tools": "/mcp/tools",
            "resources": "/mcp/resources",
            "run": "/mcp/run (POST)",
            "call_tool": "/mcp/tools/{tool_name}/call (POST)",
            "predictions": "/mcp/predictions/{request_id}",
            "stream": "/mcp/predictions/{request_id}/stream",
            "capabilities": "/cursor/capabilities"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "models_loaded": len(MODELS)}


# ==========================================================
# MCP Resource Endpoints
# ==========================================================
@app.get("/mcp/resources")
async def list_resources():
    """MCP: List available resources (models)"""
    resources = []
    for model in MODELS:
        resources.append({
            "uri": f"muapi://{model['name']}",
            "name": model["name"],
            "description": model["description"],
            "mimeType": "application/json"
        })
    return {"resources": resources}


@app.get("/mcp/resources/{model_name}")
async def get_resource(model_name: str):
    """MCP: Get specific model resource"""
    model = next((m for m in MODELS if m["name"] == model_name), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "uri": f"muapi://{model_name}",
        "contents": [{
            "uri": f"muapi://{model_name}",
            "mimeType": "application/json",
            "text": json.dumps(model, indent=2)
        }]
    }


@app.get("/mcp/tools")
async def list_tools():
    """MCP: List available tools (models as tools)"""
    tools = []
    for model in MODELS:
        tool = {
            "name": model["name"],
            "description": model["description"],
            "inputSchema": model["input_schema"]
        }
        tools.append(tool)
    return {"tools": tools}


# ==========================================================
# Cursor Integration
# ==========================================================
@app.get("/cursor/capabilities")
async def cursor_capabilities():
    """Return capabilities for Cursor integration"""
    return {
        "name": "MuAPI Generator",
        "description": "Text, image, and video generation via MuAPI",
        "capabilities": {
            "canGenerate": ["text", "image", "video"],
            "supportsStreaming": True,
            "supportsAsync": True,
            "maxConcurrent": 10,
            "requiresApiKey": True
        },
        "tools": await list_tools()
    }


# ==========================================================
# Tool Execution Routes
# ==========================================================
@app.post("/mcp/run")
async def run_model(
    req: RunRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None)
):
    """Execute a model (async with background task)"""
    # Get API key from header, request body, or env
    api_key = x_api_key or req.input.pop("_api_key", None) or os.getenv("MUAPIAPP_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via x-api-key header or _api_key in input"
        )

    if not req.endpoint_url:
        model_meta = next((m for m in MODELS if m["name"] == req.model), None)
        if not model_meta:
            raise HTTPException(status_code=404, detail="Model not found")
        endpoint_url = model_meta["endpoint_url"]
        output_type = model_meta.get("output_type", "text")
    else:
        endpoint_url = req.endpoint_url
        output_type = req.output_type

    request_id = str(uuid.uuid4())
    TASKS[request_id] = {
        "status": "queued",
        "model": req.model or endpoint_url,
        "created_at": time.time()
    }

    background_tasks.add_task(
        handle_task_execution,
        request_id,
        endpoint_url,
        req.input,
        output_type,
        req.callback_url,
        api_key
    )

    return {"request_id": request_id, "status": "queued"}


@app.post("/mcp/tools/{tool_name}/call")
async def call_tool(
    tool_name: str,
    request: ToolCallRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None)
):
    """MCP: Call a tool by name"""
    model_meta = next((m for m in MODELS if m["name"] == tool_name), None)
    if not model_meta:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Get API key from header or env
    api_key = x_api_key or os.getenv("MUAPIAPP_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via x-api-key header"
        )

    request_id = str(uuid.uuid4())
    TASKS[request_id] = {
        "status": "queued",
        "model": tool_name,
        "created_at": time.time()
    }

    background_tasks.add_task(
        handle_task_execution,
        request_id,
        model_meta["endpoint_url"],
        request.arguments,
        model_meta.get("output_type", "text"),
        None,
        api_key
    )

    return {"request_id": request_id, "status": "queued"}


@app.get("/mcp/predictions/{request_id}")
async def get_prediction(request_id: str):
    """Get task status and results"""
    task = TASKS.get(request_id)
    if not task:
        raise HTTPException(status_code=404, detail="Request ID not found")
    return task


@app.get("/mcp/predictions/{request_id}/stream")
async def stream_prediction(request_id: str):
    """Stream task results as Server-Sent Events"""
    async def event_generator():
        last_status = None
        while True:
            task = TASKS.get(request_id)
            if not task:
                yield f"data: {json.dumps({'error': 'Request ID not found'})}\n\n"
                break

            if task["status"] != last_status:
                yield f"data: {json.dumps(task)}\n\n"
                last_status = task["status"]

            if task["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==========================================================
# Background Task Handler
# ==========================================================
async def handle_task_execution(
    request_id: str,
    endpoint_url: str,
    input_payload: Dict[str, Any],
    output_type: str,
    callback_url: Optional[str],
    api_key: str
):
    """Execute task asynchronously and update status"""
    client = MuApiClient(api_key=api_key)
    try:
        TASKS[request_id]["status"] = "processing"

        result = await asyncio.to_thread(
            client.run_task,
            endpoint_url,
            input_payload,
            output_type
        )

        TASKS[request_id] = {
            "status": "completed",
            "result": result,
            "model": TASKS[request_id].get("model"),
            "created_at": TASKS[request_id].get("created_at"),
            "completed_at": time.time()
        }

        if callback_url:
            try:
                requests.post(callback_url, json=TASKS[request_id], timeout=10)
            except Exception as e:
                print(f"⚠️ Callback failed: {e}")

    except Exception as e:
        TASKS[request_id] = {
            "status": "failed",
            "error": str(e),
            "model": TASKS[request_id].get("model"),
            "created_at": TASKS[request_id].get("created_at"),
            "failed_at": time.time()
        }
        print(f"❌ Task {request_id} failed: {e}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
