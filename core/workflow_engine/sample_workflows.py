"""Sample Workflows & DataProducts für Handwerk und Recherche (Demo & Test)."""

from __future__ import annotations

from typing import Any
from pydantic import Field
from sdk.dataproduct import DataProduct
from .generic_runner import register_workflow


# 1. Handwerk Angebot Workflow
class AngebotInput(DataProduct):
    kunden_name: str = Field(description="Name des Kunden")
    projekt_titel: str = Field(description="Bezeichnung des Bau-/Handwerk-Projekts")
    umfang_qm: float = Field(default=50.0, description="Fläche in qm")
    stundensatz: float = Field(default=65.0, description="Stundensatz in EUR")


class AngebotOutput(DataProduct):
    storage_target: list[str] = ["G", "K"]
    kunden_name: str
    projekt_titel: str
    netto_gesamt: float
    brutto_gesamt: float
    angebot_text: str


async def handle_angebot_workflow(input_dp: AngebotInput) -> AngebotOutput:
    stunden = input_dp.umfang_qm * 0.5
    netto = (stunden * input_dp.stundensatz) + (input_dp.umfang_qm * 12.0)
    brutto = netto * 1.19
    text = (
        f"Angebot für {input_dp.kunden_name}:\n"
        f"Projekt: {input_dp.projekt_titel} ({input_dp.umfang_qm} qm)\n"
        f"Gesamtpreis netto: {netto:.2f} EUR | brutto: {brutto:.2f} EUR"
    )
    return AngebotOutput(
        tenant_id=input_dp.tenant_id,
        produced_by="handwerk-angebot-agent",
        workflow_run_id=input_dp.workflow_run_id,
        kunden_name=input_dp.kunden_name,
        projekt_titel=input_dp.projekt_titel,
        netto_gesamt=round(netto, 2),
        brutto_gesamt=round(brutto, 2),
        angebot_text=text,
    )


# Registrieren
register_workflow(
    workflow_id="handwerk-angebot",
    name="Handwerk Angebot Erstellung",
    description="Erstellt ein kalkuliertes Angebot für Handwerksleistungen",
    input_schema=AngebotInput,
    output_schema=AngebotOutput,
    handler=handle_angebot_workflow,
)
