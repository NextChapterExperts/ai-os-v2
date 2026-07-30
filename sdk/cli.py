"""AI-OS v2 Agent SDK CLI — Scaffolding Tool für neue Agenten und Workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AGENT_TEMPLATE = '''"""
{title_name} Agent — AI-OS v2
"""
from sdk.agent_base import AgentBase
from sdk.dataproduct import DataProduct
from pydantic import Field

class {class_name}Input(DataProduct):
    query: str = Field(description="Suchanfrage oder Arbeitsauftrag")

class {class_name}Output(DataProduct):
    summary: str = Field(description="Zusammenfassung des Ergebnisses")
    storage_target: list[str] = ["G"]

class {class_name}Agent(AgentBase[{class_name}Input, {class_name}Output]):
    agent_id = "{agent_id}"
    version = "1.0.0"
    input_schema = {class_name}Input
    output_schema = {class_name}Output

    async def run(self, input_dp: {class_name}Input) -> {class_name}Output:
        # Externe Werkzeugaufrufe über self.mcp
        # LLM-Aufrufe über self.ctx.llm
        summary_text = f"Verarbeitet: {{input_dp.query}}"
        return {class_name}Output(
            tenant_id=self.ctx.tenant_id,
            produced_by=self.agent_id,
            summary=summary_text,
        )
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-OS v2 Scaffolding CLI")
    subparsers = parser.add_subparsers(dest="command")

    new_agent_p = subparsers.add_parser("new-agent", help="Erstellt einen neuen Fachagenten-Contract")
    new_agent_p.add_argument("name", help="Name des Agenten (z. B. competitor-analysis)")
    new_agent_p.add_argument("--dir", default="agents", help="Zielverzeichnis")

    args = parser.parse_args()
    if args.command == "new-agent":
        name = args.name.lower().replace("_", "-")
        agent_id = f"{name}-agent"
        class_name = "".join(part.capitalize() for part in name.split("-"))
        title_name = class_name

        target_dir = Path(args.dir) / name
        target_dir.mkdir(parents=True, exist_ok=True)
        agent_file = target_dir / "agent.py"
        agent_file.write_text(
            AGENT_TEMPLATE.format(
                title_name=title_name,
                class_name=class_name,
                agent_id=agent_id,
            ),
            encoding="utf-8",
        )
        print(f"✓ Agent-Contract erstellt unter {agent_file}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
