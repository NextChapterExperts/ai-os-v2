"""Memory Gateway Client — LiteLLM mit Ollama-Fallback + Persist-Hook."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from .audit import write_llm_audit
from .config import LITELLM_URL, get_mode, model_for_mode, ollama_chat_url
from .langfuse_hook import trace_llm_completion
from .persist import persist_chat_turn

log = logging.getLogger("memory_gateway.client")

DEFAULT_TIMEOUT = 120.0


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        msg = data.get("message") or {}
        return _message_text(msg)
    msg = choices[0].get("message") or {}
    return _message_text(msg)


def _looks_like_thinking_leak(text: str) -> bool:
    lower = text.lower().strip()
    if not lower:
        return True
    markers = (
        "here's a thinking process",
        "thinking process",
        "analyze user input",
        "the user wants",
        "we need to answer",
        "let's craft",
        "make sure each bullet",
        "user safety:",
        "okay, let's tackle",
    )
    return any(m in lower for m in markers)


def _message_text(msg: dict[str, Any]) -> str:
    content = str(msg.get("content") or "").strip()
    if content and not _looks_like_thinking_leak(content):
        return content
    for key in ("reasoning_content", "thinking"):
        text = str(msg.get(key) or "").strip()
        if text and not _looks_like_thinking_leak(text):
            return text
    return content


def _prompt_preview(messages: list[dict[str, Any]]) -> str:
    parts = []
    for m in messages[-4:]:
        role = m.get("role", "?")
        content = str(m.get("content") or "")[:200]
        parts.append(f"[{role}] {content}")
    return "\n".join(parts)


async def _call_litellm(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 512,
    stream: bool = False,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        res = await client.post(f"{LITELLM_URL.rstrip('/')}/v1/chat/completions", json=payload)
        res.raise_for_status()
        return res.json()


async def _call_ollama_direct(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 512,
    timeout: float = 60.0,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=3.0, read=timeout)) as client:
        res = await client.post(
            ollama_chat_url(),
            json={
                "model": model,
                "stream": False,
                "keep_alive": "30m",
                "messages": messages,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        res.raise_for_status()
        data = res.json()
        content = _extract_content(data)
        return {
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {},
            "_source": "ollama-direct",
        }


async def _call_vllm_direct(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 512,
    timeout: float = 60.0,
) -> dict[str, Any]:
    from .config import vllm_chat_url
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=3.0, read=timeout)) as client:
        res = await client.post(
            vllm_chat_url(),
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        res.raise_for_status()
        data = res.json()
        data["_source"] = "vllm-direct"
        return data


async def chat_completion(
    messages: list[dict[str, Any]],
    *,
    tenant_id: str = "nextchapter",
    model: str | None = None,
    compute_mode: str | None = None,
    produced_by: str = "memory-gateway",
    intent: str = "general_chat",
    session_id: str | None = None,
    project_id: str | None = None,
    user_id: str = "peter",
    temperature: float = 0.2,
    max_tokens: int = 512,
    persist: bool = True,
) -> dict[str, Any]:
    """Ein LLM-Call über eine Tür — mit Pflicht-Persist-Hook danach."""
    mode = get_mode(compute_mode)
    resolved_model = model or model_for_mode(mode)
    sid = session_id or str(uuid.uuid4())
    sovereign_alias = model_for_mode(mode)
    is_sovereign_mode = mode == "auto" or mode.startswith("sovereign")
    use_ollama_direct = is_sovereign_mode and mode != "sovereign_vllm" and (
        model is None or resolved_model.startswith("ollama/") or resolved_model.startswith("ai-os-") or resolved_model == sovereign_alias
    )

    data: dict[str, Any] = {}
    source = "unknown"

    if mode in ("auto", "sovereign", "sovereign_vllm", "sovereign_coder"):
        from .config import VLLM_MODEL
        target_vllm_model = VLLM_MODEL
        try:
            data = await _call_vllm_direct(
                target_vllm_model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=5.0,
            )
            source = "vllm-direct"
            resolved_model = target_vllm_model
        except Exception as exc:
            log.warning(f"vLLM direkt fehlgeschlagen ({target_vllm_model}): {exc} — versuche Fallbacks")

    if not data and use_ollama_direct:
        from .config import MODE_TO_OLLAMA_MODEL, OLLAMA_MODEL, resolve_auto_model

        if mode == "auto":
            prompt_text = " ".join(str(m.get("content") or "") for m in messages)
            target_ollama_model = resolve_auto_model(prompt_text)
        else:
            target_ollama_model = MODE_TO_OLLAMA_MODEL.get(mode, OLLAMA_MODEL)

        try:
            data = await _call_ollama_direct(
                target_ollama_model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=5.0,
            )
            source = "ollama-direct"
            resolved_model = target_ollama_model
        except Exception as exc:
            log.warning(f"Ollama direkt ({target_ollama_model}) fehlgeschlagen: {exc} — versuche LiteLLM")
            try:
                data = await _call_litellm(
                    resolved_model,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                source = "litellm"
            except Exception as exc2:
                log.warning(f"Sowohl Ollama als auch LiteLLM fehlgeschlagen: {exc2} — Offline Fallback")
                data = {
                    "model": resolved_model,
                    "choices": [{"message": {"role": "assistant", "content": "Inferenz nicht erreichbar (Ollama/LiteLLM offline)"}}],
                    "usage": {},
                    "_source": "offline-fallback",
                }
                source = "offline-fallback"
    else:
        try:
            data = await _call_litellm(
                resolved_model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            source = "litellm"
        except Exception:
            log.warning("LiteLLM fehlgeschlagen — Fallback Ollama direkt")
            try:
                from .config import OLLAMA_MODEL

                data = await _call_ollama_direct(
                    OLLAMA_MODEL,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                source = "ollama-direct"
                resolved_model = data.get("model", resolved_model)
            except Exception:
                log.warning("Sowohl LiteLLM als auch Ollama direkt nicht erreichbar — Offline Fallback")
                data = {
                    "model": resolved_model,
                    "choices": [{"message": {"role": "assistant", "content": "Inferenz nicht erreichbar (LiteLLM/Ollama offline)"}}],
                    "usage": {},
                    "_source": "offline-fallback",
                }
                source = "offline-fallback"

    content = _extract_content(data)
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}

    persist_result: dict[str, Any] | None = None
    audit_hash: str | None = None
    langfuse_ok = False

    if persist:
        persist_result = persist_chat_turn(
            tenant_id,
            messages,
            content,
            session_id=sid,
            produced_by=produced_by,
            model=resolved_model,
            project_id=project_id,
        )
        audit_hash = write_llm_audit(
            tenant_id,
            model=resolved_model,
            produced_by=produced_by,
            session_id=sid,
            prompt_preview=_prompt_preview(messages),
            response_preview=content,
            usage=usage,
            compute_mode=mode,
        )
        langfuse_ok = trace_llm_completion(
            tenant_id=tenant_id,
            model=resolved_model,
            produced_by=produced_by,
            session_id=sid,
            prompt_preview=_prompt_preview(messages),
            response_preview=content,
            usage=usage,
        )

    return {
        "content": content,
        "model": resolved_model,
        "compute_mode": mode,
        "session_id": sid,
        "source": source,
        "usage": usage,
        "persist": persist_result,
        "audit_hash": audit_hash,
        "langfuse_traced": langfuse_ok,
        "raw": data,
    }


async def list_models() -> dict[str, Any]:
    """Modelle von LiteLLM + Compute-Modi aus config/compute.yaml."""
    from .config import compute_mode_snapshot, list_compute_modes

    models: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{LITELLM_URL.rstrip('/')}/v1/models")
            if res.is_success:
                body = res.json()
                models = body.get("data") or []
    except Exception:
        log.exception("LiteLLM /v1/models nicht erreichbar")

    snapshot = compute_mode_snapshot()
    return {
        **snapshot,
        "default_mode": snapshot["active_mode"],
        "default_model": snapshot["active_model"],
        "modes": list_compute_modes(),
        "models": models,
    }
