from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentOrientationInfo(BaseModel):
    """
    Orientation information of the original image BEFORE any automatic rotation.
    Separates cardinal rotation angle (0, 90, 180, 270), mirror state, and perspective/skew tilt.
    """
    angle: int = Field(
        default=0,
        description="Original cardinal rotation angle in degrees: 0, 90, 180, or 270",
    )
    status: str = Field(
        default="NORMAL",
        description="NORMAL | ROTATED_90 | INVERTED | ROTATED_270 | MIRROR | MIXED_ORIENTATION | UNKNOWN",
    )
    confidence: float = Field(
        default=0.0,
        description="Overall confidence of orientation detection [0.0, 1.0]",
    )
    is_mirrored: bool = Field(
        default=False,
        description="True if horizontal left-right mirror flip is detected",
    )
    skew_angle: float = Field(
        default=0.0,
        description="Continuous geometric tilt/skew angle in degrees (-45, +45] relative to cardinal axis",
    )
    is_tilted: bool = Field(
        default=False,
        description="True if abs(skew_angle) exceeds the tilt warning threshold",
    )
    has_mixed_orientations: bool = Field(
        default=False,
        description="True if text lines on the label have conflicting orientations",
    )
    doc_model_angle: int = Field(
        default=0,
        description="Raw angle predicted by whole-document PP-LCNet_x1_0_doc_ori classifier",
    )
    doc_model_confidence: float = Field(
        default=0.0,
        description="Raw confidence from whole-document PP-LCNet_x1_0_doc_ori classifier",
    )


class TextLineResult(BaseModel):
    """OCR and orientation result for an individual text line on the original image."""
    line_id: int = Field(..., description="0-based index of the detected text line")
    text: str = Field(..., description="Recognized text string")
    confidence: float = Field(..., description="OCR recognition confidence [0.0, 1.0]")
    angle: int = Field(
        ...,
        description="Original cardinal rotation angle of this line: 0, 90, 180, or 270",
    )
    orientation_status: str = Field(
        ...,
        description="Line orientation status: NORMAL | ROTATED_90 | INVERTED | ROTATED_270 | MIRROR",
    )
    orientation_confidence: float = Field(
        ...,
        description="Confidence of this line's orientation classification [0.0, 1.0]",
    )
    is_mirrored: bool = Field(
        default=False,
        description="True if this specific text line is horizontally mirrored",
    )
    skew_angle: float = Field(
        default=0.0,
        description="Continuous tilt/skew angle of this line in degrees (-45, +45]",
    )
    bbox: List[int] = Field(
        ...,
        description="Axis-aligned bounding box [x1, y1, x2, y2] on the ORIGINAL image",
    )
    polygon: List[List[int]] = Field(
        default_factory=list,
        description="4-point oriented bounding polygon [[x0,y0],[x1,y1],[x2,y2],[x3,y3]] on the ORIGINAL image",
    )
    candidate_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Diagnostic scores across candidate hypotheses (0/90, 180/270, mirror)",
    )
    candidate_texts: Dict[str, str] = Field(
        default_factory=dict,
        description="Recognized texts across candidate hypotheses",
    )


class OCRInspectionResult(BaseModel):
    """Complete output schema for industrial OCR and orientation inspection."""
    image: str = Field(..., description="Image file name")
    image_path: str = Field(default="", description="Full path to the inspected image")
    success: bool = Field(default=True, description="Whether OCR detection & recognition succeeded")
    total_lines: int = Field(default=0, description="Total number of recognized text lines")
    orientation: DocumentOrientationInfo = Field(
        default_factory=DocumentOrientationInfo,
        description="Global document/label orientation before any correction",
    )
    texts: List[TextLineResult] = Field(
        default_factory=list,
        description="Per-line OCR and orientation details",
    )
    result: str = Field(
        default="NG",
        description="Industrial judgement: OK (upright 0°, not mirrored) or NG (rotated/inverted/mirrored/empty)",
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation of the OK/NG judgement",
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Total end-to-end processing time in milliseconds",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed",
    )

    def to_compact_dict(self) -> Dict[str, Any]:
        """
        Return the exact dictionary structure illustrated in Section 6 of the specification,
        enriched with the full diagnostic fields.
        """
        return {
            "image": self.image,
            "success": self.success,
            "total_lines": self.total_lines,
            "orientation": {
                "angle": self.orientation.angle,
                "status": self.orientation.status,
                "confidence": round(self.orientation.confidence, 4),
                "is_mirrored": self.orientation.is_mirrored,
                "skew_angle": self.orientation.skew_angle,
                "is_tilted": self.orientation.is_tilted,
                "has_mixed_orientations": self.orientation.has_mixed_orientations,
                "doc_model_angle": self.orientation.doc_model_angle,
                "doc_model_confidence": round(self.orientation.doc_model_confidence, 4),
            },
            "texts": [
                {
                    "line_id": item.line_id,
                    "text": item.text,
                    "confidence": round(item.confidence, 4),
                    "angle": item.angle,
                    "status": item.orientation_status,
                    "orientation_confidence": round(item.orientation_confidence, 4),
                    "is_mirrored": item.is_mirrored,
                    "skew_angle": item.skew_angle,
                    "bbox": item.bbox,
                    "polygon": item.polygon,
                }
                for item in self.texts
            ],
            "result": self.result,
            "reason": self.reason,
            "processing_time_ms": round(self.processing_time_ms, 2),
        }
