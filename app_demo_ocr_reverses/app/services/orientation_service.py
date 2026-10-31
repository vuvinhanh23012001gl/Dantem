from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.constants import (
    ANGLE_TO_STATUS,
    InspectionJudgement,
    OrientationStatus,
    STATUS_LABELS_VI,
)
from app.models.orientation_engine import OrientationEngine
from app.schemas.ocr_schema import DocumentOrientationInfo, TextLineResult


class OrientationService:
    """
    Service responsible for:
    1. Resolving per-line orientation (0°, 90°, 180°, 270°, Mirror) and separating
       cardinal rotation from perspective/mounting skew angle.
    2. Aggregating line-level and document-level orientations into a final
       industrial inspection judgement (OK / NG) without losing original orientation info.
    """

    def __init__(
        self,
        orientation_engine: OrientationEngine,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.engine = orientation_engine
        cfg = (config or {}).get("orientation", {})
        self.vertical_aspect_ratio_thresh: float = float(
            cfg.get("vertical_aspect_ratio_thresh", 1.5)
        )
        self.skew_warning_deg: float = float(cfg.get("skew_warning_deg", 5.0))
        self.mirror_score_margin: float = float(cfg.get("mirror_score_margin", 0.08))
        self.mirror_min_rec_score: float = float(cfg.get("mirror_min_rec_score", 0.72))
        self.enable_mirror_detection: bool = bool(
            cfg.get("enable_mirror_detection", True)
        )

    def resolve_line_orientation(
        self,
        line_id: int,
        is_vertical: bool,
        skew_angle: float,
        bbox: List[int],
        polygon: List[List[int]],
        ori_c0: Tuple[int, float, float],
        ori_cm0: Tuple[int, float, float],
        rec_c0: Tuple[str, float],
        rec_c180: Tuple[str, float],
        rec_cm0: Tuple[str, float],
        rec_cm180: Tuple[str, float],
    ) -> Optional[TextLineResult]:
        """
        Evaluate 4 candidate hypotheses for a single cropped text line:
        - c0: Direct 0° (if horizontal) or 90° CW (if vertical)
        - c180: Direct 180° (if horizontal) or 270° CW (if vertical)
        - cm0: Mirrored 0° (if horizontal) or Mirrored 90° (if vertical)
        - cm180: Mirrored 180° (if horizontal) or Mirrored 270° (if vertical)
        """
        _, prob_0, prob_180 = ori_c0
        _, prob_m0_0, prob_m0_180 = ori_cm0

        text_0, score_0 = rec_c0
        text_180, score_180 = rec_c180
        text_m0, score_m0 = rec_cm0
        text_m180, score_m180 = rec_cm180

        lex_0 = self.engine.compute_lexical_quality(text_0)
        lex_180 = self.engine.compute_lexical_quality(text_180)
        lex_m0 = self.engine.compute_lexical_quality(text_m0)
        lex_m180 = self.engine.compute_lexical_quality(text_m180)

        # Composite scores combining OCR confidence, textline orientation classifier, and lexical quality
        comp_0 = 0.55 * score_0 + 0.35 * prob_0 + 0.10 * lex_0
        comp_180 = 0.55 * score_180 + 0.35 * prob_180 + 0.10 * lex_180
        comp_m0 = 0.55 * score_m0 + 0.35 * prob_m0_0 + 0.10 * lex_m0
        comp_m180 = 0.55 * score_m180 + 0.35 * prob_m0_180 + 0.10 * lex_m180

        # If recognition score difference between 0 and 180 is very large (>0.22),
        # give higher priority to the recognition model's confidence.
        if score_180 - score_0 >= 0.22:
            direct_is_180 = True
        elif score_0 - score_180 >= 0.22:
            direct_is_180 = False
        else:
            direct_is_180 = comp_180 > comp_0

        if not direct_is_180:
            best_direct_angle = 90 if is_vertical else 0
            best_direct_text = text_0
            best_direct_rec_score = score_0
            best_direct_ori_conf = float(max(prob_0, score_0))
            best_direct_lex = lex_0
        else:
            best_direct_angle = 270 if is_vertical else 180
            best_direct_text = text_180
            best_direct_rec_score = score_180
            best_direct_ori_conf = float(max(prob_180, score_180))
            best_direct_lex = lex_180

        # Best mirrored hypothesis
        if score_m180 - score_m0 >= 0.22:
            mirror_is_180 = True
        elif score_m0 - score_m180 >= 0.22:
            mirror_is_180 = False
        else:
            mirror_is_180 = comp_m180 > comp_m0

        if not mirror_is_180:
            best_mir_angle = 90 if is_vertical else 0
            best_mir_text = text_m0
            best_mir_rec_score = score_m0
            best_mir_ori_conf = float(max(prob_m0_0, score_m0))
            best_mir_lex = lex_m0
        else:
            best_mir_angle = 270 if is_vertical else 180
            best_mir_text = text_m180
            best_mir_rec_score = score_m180
            best_mir_ori_conf = float(max(prob_m0_180, score_m180))
            best_mir_lex = lex_m180

        # Decide whether the line is horizontally mirrored
        is_mirrored = False
        if (
            self.enable_mirror_detection
            and best_mir_text
            and not self.engine.is_horizontally_palindrome_symmetric(best_mir_text)
            and best_mir_rec_score >= self.mirror_min_rec_score
        ):
            rec_diff = best_mir_rec_score - best_direct_rec_score
            lex_diff = best_mir_lex - best_direct_lex
            if rec_diff >= self.mirror_score_margin:
                is_mirrored = True
            elif rec_diff >= 0.03 and lex_diff >= 0.12:
                is_mirrored = True

        if is_mirrored:
            final_text = best_mir_text
            final_rec_conf = best_mir_rec_score
            final_angle = best_mir_angle
            final_status = OrientationStatus.MIRROR.value
            final_ori_conf = best_mir_ori_conf
        else:
            final_text = best_direct_text
            final_rec_conf = best_direct_rec_score
            final_angle = best_direct_angle
            final_status = ANGLE_TO_STATUS.get(
                final_angle, OrientationStatus.NORMAL.value
            )
            final_ori_conf = best_direct_ori_conf

        if not final_text:
            return None

        candidate_scores = {
            "direct_0_or_90": round(score_0, 4),
            "direct_180_or_270": round(score_180, 4),
            "mirror_0_or_90": round(score_m0, 4),
            "mirror_180_or_270": round(score_m180, 4),
            "line_ori_prob_0": round(prob_0, 4),
            "line_ori_prob_180": round(prob_180, 4),
        }
        candidate_texts = {
            "direct_0_or_90": text_0,
            "direct_180_or_270": text_180,
            "mirror_0_or_90": text_m0,
            "mirror_180_or_270": text_m180,
        }

        return TextLineResult(
            line_id=line_id,
            text=final_text,
            confidence=round(final_rec_conf, 4),
            angle=final_angle,
            orientation_status=final_status,
            orientation_confidence=round(final_ori_conf, 4),
            is_mirrored=is_mirrored,
            skew_angle=skew_angle,
            bbox=bbox,
            polygon=polygon,
            candidate_scores=candidate_scores,
            candidate_texts=candidate_texts,
        )

    def aggregate_document_orientation(
        self,
        lines: List[TextLineResult],
        doc_model_angle: int,
        doc_model_confidence: float,
    ) -> Tuple[DocumentOrientationInfo, str, str]:
        """
        Aggregate per-line orientations and the whole-document classifier prediction
        into a unified DocumentOrientationInfo, OK/NG judgement, and reason string.
        """
        if not lines:
            status = ANGLE_TO_STATUS.get(
                doc_model_angle, OrientationStatus.UNKNOWN.value
            )
            doc_info = DocumentOrientationInfo(
                angle=doc_model_angle,
                status=OrientationStatus.UNKNOWN.value,
                confidence=round(doc_model_confidence, 4),
                is_mirrored=False,
                skew_angle=0.0,
                is_tilted=False,
                has_mixed_orientations=False,
                doc_model_angle=doc_model_angle,
                doc_model_confidence=round(doc_model_confidence, 4),
            )
            return (
                doc_info,
                InspectionJudgement.NG.value,
                "Không phát hiện hoặc không đọc được dòng chữ nào trên ảnh.",
            )

        # Weight each line by its character count and confidence
        status_weights: Counter = Counter()
        angle_weights: Counter = Counter()
        distinct_statuses = set()

        for line in lines:
            char_weight = max(1, min(len(line.text.strip()), 15)) * max(
                line.confidence, 0.3
            )
            status_weights[line.orientation_status] += char_weight
            angle_weights[line.angle] += char_weight
            # Ignore 1-character symmetric tokens when checking mixed orientations
            if len(line.text.strip()) >= 2 or not self.engine.is_horizontally_palindrome_symmetric(
                line.text
            ):
                distinct_statuses.add(line.orientation_status)

        dominant_status, dominant_weight = status_weights.most_common(1)[0]
        dominant_angle, _ = angle_weights.most_common(1)[0]
        total_weight = sum(status_weights.values())

        # Map status to candidate_scores key for ambiguity verification
        status_to_cand_key = {
            OrientationStatus.NORMAL.value: "direct_0_or_90",
            OrientationStatus.ROTATED_90.value: "direct_0_or_90",
            OrientationStatus.INVERTED.value: "direct_180_or_270",
            OrientationStatus.ROTATED_270.value: "direct_180_or_270",
            OrientationStatus.MIRROR.value: "mirror_0_or_90",
        }

        # Harmonize only truly ambiguous/symmetric short tokens when >=75% weight agrees,
        # while preserving genuinely mixed-orientation lines where scores strongly diverge.
        if total_weight > 0 and (dominant_weight / total_weight) >= 0.72 and len(lines) >= 2:
            dom_cand_key = status_to_cand_key.get(dominant_status, "")
            for line in lines:
                if line.orientation_status != dominant_status:
                    dom_score = line.candidate_scores.get(dom_cand_key, 0.0)
                    is_short_or_sym = (
                        len(line.text.strip()) <= 2
                        or self.engine.is_horizontally_palindrome_symmetric(line.text)
                    )
                    is_close_score = (
                        dom_score >= 0.80 and (line.confidence - dom_score) <= 0.08
                    )
                    if is_short_or_sym or is_close_score:
                        line.orientation_status = dominant_status
                        line.angle = dominant_angle
                        line.is_mirrored = (
                            dominant_status == OrientationStatus.MIRROR.value
                        )
                        dom_text = line.candidate_texts.get(dom_cand_key, "")
                        if dom_text:
                            line.text = dom_text
                            line.confidence = round(dom_score, 4)

        distinct_statuses = {
            line.orientation_status
            for line in lines
            if len(line.text.strip()) >= 2
            or not self.engine.is_horizontally_palindrome_symmetric(line.text)
        }
        if not distinct_statuses and lines:
            distinct_statuses = {lines[0].orientation_status}

        has_mixed = len(distinct_statuses) > 1
        is_mirrored = any(line.is_mirrored for line in lines) and (
            dominant_status == OrientationStatus.MIRROR.value or has_mixed
        )

        # Compute median skew angle across lines
        skew_values = [line.skew_angle for line in lines]
        median_skew = float(round(float(np.median(skew_values)), 2))
        is_tilted = abs(median_skew) >= self.skew_warning_deg

        mean_ori_conf = float(
            np.mean([line.orientation_confidence for line in lines])
        )

        if has_mixed:
            final_doc_status = OrientationStatus.MIXED.value
        else:
            final_doc_status = dominant_status

        doc_info = DocumentOrientationInfo(
            angle=dominant_angle,
            status=final_doc_status,
            confidence=round(mean_ori_conf, 4),
            is_mirrored=dominant_status == OrientationStatus.MIRROR.value,
            skew_angle=median_skew,
            is_tilted=is_tilted,
            has_mixed_orientations=has_mixed,
            doc_model_angle=doc_model_angle,
            doc_model_confidence=round(doc_model_confidence, 4),
        )

        # Industrial Inspection Judgement (OK vs NG)
        # OK requires: all informative lines are NORMAL (0°, not mirrored, not mixed)
        if (
            final_doc_status == OrientationStatus.NORMAL.value
            and not has_mixed
            and not doc_info.is_mirrored
        ):
            judgement = InspectionJudgement.OK.value
            if is_tilted:
                reason = (
                    f"Chữ đúng chiều (0°), có độ nghiêng phối cảnh nhẹ ({median_skew:+.1f}°)."
                )
            else:
                reason = "Tất cả các dòng chữ đều đúng chiều chuẩn (0°)."
        else:
            judgement = InspectionJudgement.NG.value
            if has_mixed:
                status_summary = ", ".join(
                    f"Dòng #{l.line_id + 1}: {l.orientation_status} ({l.angle}°)"
                    for l in lines
                )
                reason = f"Phát hiện tem có nhiều dòng chữ ngược/khác hướng nhau: {status_summary}."
            else:
                vi_label = STATUS_LABELS_VI.get(final_doc_status, final_doc_status)
                reason = f"Phát hiện chữ sai chiều chuẩn: {vi_label} (Góc={dominant_angle}°)."

        return doc_info, judgement, reason
