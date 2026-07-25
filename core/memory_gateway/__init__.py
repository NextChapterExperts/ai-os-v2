"""Memory Gateway — eine Inference-Tür mit Persist-Hook (P11/P19, Phase 1).

Alle LLM-Calls laufen über LiteLLM (:4000) oder Fallback Ollama direkt;
nach jedem Completion: Memory-Trail (SQLite) + Audit (ai_os_log) + optional LangFuse.
"""

from .client import chat_completion, list_models
from .persist import persist_chat_turn

__all__ = ["chat_completion", "list_models", "persist_chat_turn"]
