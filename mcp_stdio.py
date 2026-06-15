import asyncio
import json
import os
import time
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

API_BASE = "https://api.muapi.ai"

app = Server("muapi")

TOOLS = [
    Tool(
        name="generate_image",
        description="Generate an image using AI models (FLUX, Midjourney v7, GPT-4o, HiDream, Reve, Wan2.1) via MuAPI",
        inputSchema={
            "type": "object",
            "properties": {
                "endpoint_url": {"type": "string", "description": "MuAPI endpoint URL for the model"},
                "prompt": {"type": "string", "description": "Text prompt for image generation"},
                "width": {"type": "integer", "description": "Image width in pixels", "default": 1024},
                "height": {"type": "integer", "description": "Image height in pixels", "default": 1024},
            },
            "required": ["endpoint_url", "prompt"],
        },
    ),
    Tool(
        name="generate_video",
        description="Generate a video using AI models (Veo3, Kling 3.0, HunyuanVideo, Runway, Pixverse, SeedDance) via MuAPI",
        inputSchema={
            "type": "object",
            "properties": {
                "endpoint_url": {"type": "string", "description": "MuAPI endpoint URL for the model"},
                "prompt": {"type": "string", "description": "Text prompt for video generation"},
                "duration": {"type": "number", "description": "Video duration in seconds", "default": 5},
            },
            "required": ["endpoint_url", "prompt"],
        },
    ),
    Tool(
        name="generate_audio",
        description="Generate music or sound effects using AI models (Suno, MMAudio) via MuAPI",
        inputSchema={
            "type": "object",
            "properties": {
                "endpoint_url": {"type": "string", "description": "MuAPI endpoint URL for the model"},
                "prompt": {"type": "string", "description": "Text prompt for audio generation"},
            },
            "required": ["endpoint_url", "prompt"],
        },
    ),
    Tool(
        name="edit_image",
        description="Edit an image using AI (lipsync, upscale, background removal, face swap, Ghibli style) via MuAPI",
        inputSchema={
            "type": "object",
            "properties": {
                "endpoint_url": {"type": "string", "description": "MuAPI endpoint URL for the editing model"},
                "image_url": {"type": "string", "description": "URL of the source image to edit"},
                "prompt": {"type": "string", "description": "Editing instruction or prompt"},
            },
            "required": ["endpoint_url", "image_url"],
        },
    ),
    Tool(
        name="get_prediction",
        description="Poll the result of an async MuAPI generation request by request_id",
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The request_id returned from a generation call"},
            },
            "required": ["request_id"],
        },
    ),
    Tool(
        name="account_balance",
        description="Get the current MuAPI account credit balance",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


def _headers():
    return {
        "x-api-key": os.getenv("MUAPIAPP_API_KEY", ""),
        "Content-Type": "application/json",
    }


def _poll(request_id: str, timeout: int = 120) -> dict:
    url = f"{API_BASE}/api/v1/predictions/{request_id}/result"
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(url, headers=_headers(), timeout=30)
        data = r.json()
        status = data.get("status")
        if status == "completed":
            return data
        if status == "failed":
            return {"error": data.get("error", "generation failed"), "status": "failed"}
        time.sleep(2)
    return {"error": "timed out waiting for result", "status": "timeout"}


@app.list_tools()
async def list_tools():
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "account_balance":
            r = requests.get(f"{API_BASE}/api/v1/account/balance", headers=_headers(), timeout=30)
            return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]

        if name == "get_prediction":
            result = _poll(arguments["request_id"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        endpoint_url = arguments.get("endpoint_url", "")
        payload = {k: v for k, v in arguments.items() if k != "endpoint_url"}
        r = requests.post(endpoint_url, headers=_headers(), json=payload, timeout=60)
        data = r.json()
        request_id = data.get("request_id")
        if request_id:
            result = _poll(request_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
