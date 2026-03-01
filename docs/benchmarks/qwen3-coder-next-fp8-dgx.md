---
title: "Qwen3-Coder-Next-FP8 on DGX Spark: Inference Benchmark"
date: 2026-03-01
author: linda
category: benchmarks
tags: [qwen3, vllm, dgx, fp8, inference-speed, coding-model]
status: published
sources:
  - url: https://huggingface.co/Qwen/Qwen3-Coder-Next-FP8
    title: "Qwen3-Coder-Next-FP8 Model Card"
related:
  - llm-infra/index.md
embeddings_ready: true
---

# Qwen3-Coder-Next-FP8 on DGX Spark: Inference Benchmark

Real numbers from the homelab DGX Spark (GB10 SoC, 120GB unified memory, Blackwell GPU, CUDA 13.0).

## Setup

| Component | Value |
|-----------|-------|
| Hardware | NVIDIA DGX Spark (GB10 SoC) |
| Memory | 120GB unified (CPU + GPU shared) |
| Runtime | vLLM v0.8+ (NGC image `nvcr.io/nvidia/vllm:26.01-py3`) |
| Model | `Qwen/Qwen3-Coder-Next-FP8` (~92GB on disk) |
| Context | 131,072 tokens (vLLM config), 262,144 (Ollama) |
| GPU memory utilization | 0.80 |
| Attention backend | FlashInfer |

## Results

| Metric | Value |
|--------|-------|
| **Throughput** | ~43 tok/s (single-stream output) |
| **TTFT** | ~2–4s for 4K input prompts |
| **Context** | 131K tokens active, 170K theoretical |
| **Memory used** | ~92GB (88GB model weights + KV cache overhead) |
| **Available after load** | ~23GB headroom for KV cache |

## Comparison

| Model | Hardware | Runtime | Speed | Context |
|-------|----------|---------|-------|---------|
| Qwen3-Coder-Next-FP8 | DGX Spark | vLLM | **43 tok/s** | 131K |
| qwen3:30b-a3b | DGX Spark | Ollama | 72.9 tok/s | 262K |
| qwen3:8b-smart | DGX Spark | Ollama | 40 tok/s | 32K |
| qwen3:8b-smart | ai-server (2× RTX 3070) | Ollama | 68 tok/s | 32K |

!!! note "Why FP8 over the 30B MoE?"
    Qwen3-Coder-Next-FP8 is a dense coding-specialist model. The 30B MoE (qwen3:30b-a3b) is faster in tok/s but generalist. For code generation, tool use, and function calling, the coding specialist wins on task accuracy — speed difference is 43 vs 72 tok/s, acceptable for interactive coding.

## Config

```ini
# /etc/systemd/system/qwen3-coder.service
[Service]
ExecStart=docker compose -f /root/qwen3-coder/docker-compose.yml up
```

```yaml
# docker-compose.yml (excerpt)
command: >
  vllm serve Qwen/Qwen3-Coder-Next-FP8
  --host 0.0.0.0
  --port 8066
  --gpu-memory-utilization 0.80
  --max-model-len 131072
  --enable-auto-tool-choice
  --tool-call-parser qwen3_coder
  --attention-backend flashinfer
```

## Operational Notes

- Service initially appeared `inactive (dead)` in systemd despite the Docker container running — `docker compose up -d` confirms healthy
- `gpt-oss-120b` (llama.cpp, ~60GB) removed 2026-03-01 to free disk; freed 103GB total
- Tool calling works out-of-the-box with `--enable-auto-tool-choice` + `--tool-call-parser qwen3_coder`
- OpenClaw agents connect via `http://dgx.homelab.lan:8066/v1` (OpenAI-compatible API)
