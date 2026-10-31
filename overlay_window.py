"""
VibeSense AI - Floating Overlay Window Module
Re-exports FloatingOverlayWindow and related components from chat_overlay.
"""

from chat_overlay import (
    FloatingOverlayWindow,
    DraftTextEdit,
    AnalysisThread,
    FitScrollArea,
)

__all__ = [
    "FloatingOverlayWindow",
    "DraftTextEdit",
    "AnalysisThread",
    "FitScrollArea",
]
