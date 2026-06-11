# MuAPI MCP Server

## Overview

**Name:** MuAPI  
**Tagline:** Generate images, videos, and audio using 100+ AI models — directly from your AI assistant  
**Homepage:** https://muapi.ai  
**Repository:** https://github.com/SamurAIGPT/muapi-mcp-server  
**License:** ISC  
**Author:** MuAPI (support@muapi.ai)  
**Category:** Media, AI, Image Generation, Video Generation, Audio  

## Description

MuAPI is a hosted MCP server that gives any MCP-compatible AI assistant instant access to 100+ generative AI models for images, videos, audio, and editing — no local installation required.

Point your client at `https://api.muapi.ai/mcp`, add your API key, and you're ready to generate. Works with Claude Code, Cursor, Windsurf, Claude Desktop, Cline, and any other MCP client.

**Models supported:** FLUX, Midjourney, Veo3, Kling, HunyuanVideo, Runway, Suno, and 90+ more.

## Tags

`image-generation` `video-generation` `audio` `ai` `flux` `midjourney` `veo3` `kling` `media` `generative-ai` `hosted` `streamable-http`

## Transport

- **Type:** Streamable HTTP (hosted)  
- **Endpoint:** `https://api.muapi.ai/mcp`  
- **Auth:** Bearer token via `Authorization` header

## Setup

**No installation required.** Add to your MCP client config:

### Claude Code
```bash
claude mcp add --transport http muapi \
  https://api.muapi.ai/mcp \
  --header "Authorization: Bearer YOUR_MUAPI_KEY"
```

### Cursor / Windsurf / Claude Desktop
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

**Get your API key:** https://muapi.ai/dashboard/keys

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MUAPI_API_KEY` | Yes | Your API key from muapi.ai/dashboard/keys |

## Tools (19 total)

### Image Generation
- `muapi_image_generate` — Generate images from text (FLUX, Midjourney, GPT-4o, HiDream, Reve, SeedDream, Wan2.1, Qwen)
- `muapi_image_edit` — Edit or transform images (FLUX Kontext, GPT-4o, Reve, SeedEdit, Midjourney)

### Video Generation
- `muapi_video_generate` — Generate videos from text (Veo3, Kling, HunyuanVideo, Runway, Pixverse, MiniMax, SeedDance)
- `muapi_video_from_image` — Animate images into videos (Veo3, Kling, Wan2.1, SeedDance, Runway, Pixverse)

### Audio
- `muapi_audio_create` — Generate music with Suno (prompt, title, tags, instrumental mode)
- `muapi_audio_from_text` — Generate sound effects or ambient audio with MMAudio

### Image Enhancement
- `muapi_enhance_upscale` — AI super-resolution upscaling
- `muapi_enhance_bg_remove` — Background removal
- `muapi_enhance_face_swap` — Face swap in images or videos
- `muapi_enhance_ghibli` — Studio Ghibli style transfer

### Video Editing
- `muapi_edit_lipsync` — Lip sync audio to video (Sync, LatentSync, Creatify, VEED)
- `muapi_edit_clipping` — Extract highlight clips from long videos

### Discovery & Async
- `search_models` — Search the full 100+ model catalog
- `muapi_predict_result` — Poll for async generation results

### Account
- `muapi_account_balance` — Check credit balance
- `muapi_account_topup` — Create Stripe checkout to add credits
- `muapi_keys_list` — List API keys
- `muapi_keys_create` — Create a new API key
- `muapi_keys_delete` — Delete an API key

## Pricing

Usage is pay-per-generation, billed in credits. No subscription required.  
Free credits available on signup.  
Top up at: https://muapi.ai/dashboard

## Links

- **Platform:** https://muapi.ai  
- **API Docs:** https://api.muapi.ai/docs  
- **Dashboard:** https://muapi.ai/dashboard  
- **npm:** https://www.npmjs.com/package/muapi-mcp-server  
- **Smithery:** https://smithery.ai/servers/am-1m1k/muapi  
- **MCP Registry:** https://registry.modelcontextprotocol.io  
