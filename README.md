# muapi MCP Server

Connect any MCP-compatible AI assistant to [muapi.ai](https://muapi.ai) — access 100+ generative AI models (image, video, audio, enhance, edit) directly from Claude, Cursor, Windsurf, and more.

[![muapi](https://img.shields.io/badge/muapi.ai-platform-blue)](https://muapi.ai)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![smithery badge](https://smithery.ai/badge/am-1m1k/muapi)](https://smithery.ai/servers/am-1m1k/muapi)

---

## Install via Smithery

The easiest way to install for any MCP client:

```bash
npx -y @smithery/cli install am-1m1k/muapi --client claude
```

Or browse the listing: [smithery.ai/servers/am-1m1k/muapi](https://smithery.ai/servers/am-1m1k/muapi)

---

## Quick Start (Hosted — Recommended)

The fastest way: use the hosted MCP server at `https://api.muapi.ai/mcp`. No installation required — just add it to your client.

**Get your API key at [muapi.ai/dashboard/keys](https://muapi.ai/dashboard/keys)**

### Claude Code

```bash
claude mcp add --transport http muapi \
  https://api.muapi.ai/mcp \
  --header "Authorization: Bearer YOUR_MUAPI_KEY"
```

### Cursor

Open `Cmd+Shift+P` → **Open MCP settings** and add to `mcp.json`:

```json
{
  "mcpServers": {
    "muapi": {
      "url": "https://api.muapi.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MUAPI_KEY"
      }
    }
  }
}
```

### Windsurf

Open **Settings → MCP** and add:

```json
{
  "mcpServers": {
    "muapi": {
      "serverUrl": "https://api.muapi.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MUAPI_KEY"
      }
    }
  }
}
```

### Claude Desktop / Other clients

Add to your MCP client config:

```json
{
  "mcpServers": {
    "muapi": {
      "url": "https://api.muapi.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MUAPI_KEY"
      }
    }
  }
}
```

---

## Self-Hosted Setup

If you want to run your own MCP server instance:

### 1. Clone the repo

```bash
git clone https://github.com/SamurAIGPT/muapi-mcp-server.git
cd muapi-mcp-server
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn requests pydantic
```

### 3. Set your API key

```bash
export MUAPIAPP_API_KEY=your_muapi_key_here
```

### 4. Start the server

```bash
python mcp_server.py
```

The server starts at `http://localhost:8000`.

### 5. Configure your client

Point your MCP client to your local server:

```json
{
  "mcpServers": {
    "muapi": {
      "url": "http://localhost:8000",
      "headers": {
        "x-api-key": "YOUR_MUAPI_KEY"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MUAPIAPP_API_KEY` | Your muapi.ai API key | required |
| `MODELS_JSON` | Path to models config JSON | `models.json` |
| `PORT` | Server port | `8000` |

---

## Available Tools

Once connected, your AI assistant has access to these tools:

### Discovery
| Tool | Description |
|------|-------------|
| `search_models` | Search muapi's 100+ model catalog by keyword or category |

### Image Generation
| Tool | Models | Description |
|------|--------|-------------|
| `muapi_image_generate` | flux-dev, flux-schnell, flux-kontext-dev/pro/max, hidream-fast/dev/full, wan2.1, reve, gpt4o, midjourney, seedream, qwen | Generate images from text prompts |
| `muapi_image_edit` | flux-kontext-dev/pro/max/effects, gpt4o, reve, seededit, midjourney, midjourney-style, midjourney-omni, qwen | Edit or transform images |

### Video Generation
| Tool | Models | Description |
|------|--------|-------------|
| `muapi_video_generate` | veo3, veo3-fast, kling-master, wan2.1/2.2, seedance-pro/lite, hunyuan, runway, pixverse, vidu, minimax-std/pro | Generate videos from text |
| `muapi_video_from_image` | veo3, veo3-fast, kling-std/pro/master, wan2.1/2.2, seedance, hunyuan, runway, pixverse, vidu, midjourney, minimax | Animate images into videos |

### Audio
| Tool | Description |
|------|-------------|
| `muapi_audio_create` | Create original music with Suno (prompt, title, tags, instrumental mode) |
| `muapi_audio_from_text` | Generate sound effects or ambient audio with MMAudio |

### Image Enhancement
| Tool | Description |
|------|-------------|
| `muapi_enhance_upscale` | AI super-resolution upscaling |
| `muapi_enhance_bg_remove` | Background removal |
| `muapi_enhance_face_swap` | Face swap in images or videos |
| `muapi_enhance_ghibli` | Studio Ghibli style transfer |

### Video Editing
| Tool | Models | Description |
|------|--------|-------------|
| `muapi_edit_lipsync` | sync, latentsync, creatify, veed | Sync lip movements to audio |
| `muapi_edit_clipping` | — | Extract highlight clips from long videos |

### Async Polling
| Tool | Description |
|------|-------------|
| `muapi_predict_result` | Poll for the result of any async generation job |

### Account & Keys
| Tool | Description |
|------|-------------|
| `muapi_account_balance` | Check your current credit balance |
| `muapi_account_topup` | Create a Stripe checkout session to add credits |
| `muapi_keys_list` | List your API keys |
| `muapi_keys_create` | Create a new API key |
| `muapi_keys_delete` | Delete an API key |

---

## Usage Examples

Once your MCP client is connected, you can ask your AI assistant naturally:

**Generate an image:**
> "Generate a photorealistic mountain lake at golden hour using flux-dev"

**Edit an image:**
> "Convert this image to Studio Ghibli style" *(attaches image URL)*

**Create a video:**
> "Make a 5-second cinematic video of a robot walking through a forest using kling-master"

**Animate an image:**
> "Turn this product photo into a 5-second video" *(attaches image URL)*

**Create music:**
> "Create a 30-second lo-fi hip hop track, instrumental"

**Check balance:**
> "What's my muapi credit balance?"

**Find models:**
> "What image generation models are available on muapi?"

---

## How Async Generation Works

Most generation tools return a `request_id` immediately:

```json
{ "request_id": "abc123", "status": "processing" }
```

Your assistant will automatically poll `muapi_predict_result` until the job completes:

```json
{
  "request_id": "abc123",
  "status": "completed",
  "outputs": ["https://cdn.muapi.ai/..."]
}
```

---

## API Reference

The self-hosted server exposes these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Server info and endpoint list |
| `GET` | `/health` | Health check |
| `GET` | `/mcp/tools` | List available tools/models |
| `POST` | `/mcp/tools/{tool_name}/call` | Call a specific tool |
| `POST` | `/mcp/run` | Run a model by name or endpoint URL |
| `GET` | `/mcp/predictions/{id}` | Get prediction status and result |
| `GET` | `/mcp/predictions/{id}/stream` | Stream prediction status as SSE |
| `GET` | `/mcp/resources` | List models as MCP resources |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

---

## Authentication

**Hosted server** — pass your API key in the `Authorization` header:
```
Authorization: Bearer YOUR_MUAPI_KEY
```

**Self-hosted server** — pass via `x-api-key` header or set `MUAPIAPP_API_KEY` environment variable.

Get your API key at [muapi.ai/dashboard/keys](https://muapi.ai/dashboard/keys).

---

## Links

- [muapi.ai](https://muapi.ai) — Platform
- [API Documentation](https://api.muapi.ai/docs) — Full REST API reference
- [muapi CLI](https://github.com/SamurAIGPT/muapi-cli) — Command-line interface
- [Dashboard](https://muapi.ai/dashboard) — Manage keys and credits
