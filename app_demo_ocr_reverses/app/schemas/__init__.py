"""Data schemas for OCR and Orientation results."""

from .ocr_schema import (
    DocumentOrientationInfo,
    OCRInspectionResult,
    TextLineResult,
)

__all__ = [
    "DocumentOrientationInfo",
    "TextLineResult",
    "OCRInspectionResult",
]
