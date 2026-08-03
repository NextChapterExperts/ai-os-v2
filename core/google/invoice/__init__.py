"""Rechnungs-Extraktion — Gmail, Drive, Sheets."""

__all__ = ["preview_invoices", "run_invoice_pipeline"]


def __getattr__(name: str):
    if name in __all__:
        from core.google.invoice import pipeline as _pipeline

        return getattr(_pipeline, name)
    raise AttributeError(name)
