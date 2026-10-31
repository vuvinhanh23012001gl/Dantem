import os
import re
from typing import Dict, List, Optional, Tuple
import numpy as np

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from paddleocr import (
    DocImgOrientationClassification,
    TextLineOrientationClassification,
)
from app.core.logger import get_logger

logger = get_logger(__name__)

# Common industrial label tokens & patterns for lexical plausibility verification
INDUSTRIAL_KEYWORDS = {
    "LOT", "BATCH", "DATE", "MFG", "EXP", "PROD", "MODEL", "MOD", "TYPE",
    "PART", "PN", "P/N", "SN", "S/N", "SERIAL", "NO", "QTY", "QUANTITY",
    "WEIGHT", "WT", "NET", "GROSS", "KG", "G", "PCS", "MADE", "IN",
    "VIETNAM", "CHINA", "JAPAN", "KOREA", "USA", "CLASS", "LASER",
    "PRODUCT", "LENOVO", "CARTON", "INSPECTOR", "CHECK", "PASS", "OK",
    "REV", "VERSION", "VER", "VOLTAGE", "220V", "240V", "110V", "50/60HZ",
    "50HZ", "60HZ", "ROHS", "ISO", "CE", "QA", "QC", "SHIFT", "LINE",
    "STOP", "EXIT", "START", "MENU", "CLEAR", "BACK", "BARCODE", "SKU",
    "SAN", "XUAT", "NGAY", "MA", "SO", "LUONG", "KIEM", "TRA", "DAT",
}

# Characters that are strictly or nearly symmetric under horizontal left-right reflection in industrial sans-serif fonts
HORIZONTALLY_SYMMETRIC_CHARS = set("AHIMOTUVWXY018+-=:._|!^\"'*<> ")

# Characters that are often hallucinated when reading upside-down or mirrored text
GARBLED_HALLUCINATION_CHARS = set("∂əіїєґ\\§¤¶")


class OrientationEngine:
    """
    Low-level wrapper around PaddleOCR's orientation classification models:
    1. PP-LCNet_x1_0_doc_ori: Whole-document orientation (0°, 90°, 180°, 270°)
    2. PP-LCNet_x1_0_textline_ori: Text-line orientation (0° vs 180°)
    Plus lexical/glyph asymmetry analysis for Mirror (Horizontal Flip) detection.
    """

    def __init__(
        self,
        doc_model_name: str = "PP-LCNet_x1_0_doc_ori",
        textline_model_name: str = "PP-LCNet_x1_0_textline_ori",
        device: Optional[str] = None,
    ) -> None:
        self.doc_model_name = doc_model_name
        self.textline_model_name = textline_model_name
        self.device = device

        logger.info(
            "Initializing OrientationEngine (doc=%s, textline=%s)...",
            doc_model_name,
            textline_model_name,
        )
        self.doc_classifier = DocImgOrientationClassification(
            model_name=doc_model_name,
            device=device,
        )
        self.textline_classifier = TextLineOrientationClassification(
            model_name=textline_model_name,
            device=device,
        )

    def classify_document(self, image: np.ndarray) -> Tuple[int, float]:
        """
        Predict whole-document cardinal orientation (0, 90, 180, 270)
        on the raw input image before any rotation.
        """
        preds = list(self.doc_classifier.predict(image))
        if not preds:
            return 0, 0.0
        res = preds[0]
        label_str = str(res["label_names"][0]).replace("_degree", "").strip()
        score = float(res["scores"][0])
        try:
            angle = int(label_str)
        except ValueError:
            angle = 0
        return angle, score

    def classify_textline_batch(
        self, crops: List[np.ndarray]
    ) -> List[Tuple[int, float, float]]:
        """
        Classify a batch of rectified horizontal text-line crops into 0° or 180°.

        Returns:
            List of tuples: (predicted_angle_0_or_180, prob_0_deg, prob_180_deg)
        """
        if not crops:
            return []
        preds = list(self.textline_classifier.predict(crops))
        results: List[Tuple[int, float, float]] = []
        for res in preds:
            label = str(res["label_names"][0])
            top_score = float(res["scores"][0])
            if "180" in label:
                pred_angle = 180
                prob_180 = top_score
                prob_0 = max(0.0, 1.0 - top_score)
            else:
                pred_angle = 0
                prob_0 = top_score
                prob_180 = max(0.0, 1.0 - top_score)
            results.append((pred_angle, prob_0, prob_180))
        return results

    @staticmethod
    def is_horizontally_palindrome_symmetric(text: str) -> bool:
        """
        Check if a string looks identical when reflected horizontally
        (i.e. all characters are horizontally symmetric AND the string is a palindrome).
        """
        cleaned = text.strip()
        if not cleaned:
            return True
        if cleaned != cleaned[::-1]:
            return False
        return all(ch in HORIZONTALLY_SYMMETRIC_CHARS for ch in cleaned.upper())

    @staticmethod
    def symmetric_char_ratio(text: str) -> float:
        """Return the fraction of characters in text that are horizontally symmetric."""
        cleaned = [ch for ch in text.strip().upper() if not ch.isspace()]
        if not cleaned:
            return 1.0
        sym_count = sum(1 for ch in cleaned if ch in HORIZONTALLY_SYMMETRIC_CHARS)
        return sym_count / float(len(cleaned))

    @staticmethod
    def compute_lexical_quality(text: str) -> float:
        """
        Compute a lexical & structural plausibility score in [0.0, 1.0] for industrial labels.
        Helps disambiguate 0° vs 180° vs Mirror when OCR attempts to read upside-down glyphs.
        """
        s = text.strip()
        if not s:
            return 0.0

        score = 0.50
        upper_s = s.upper()

        # Penalize known hallucination characters from upside-down/mirrored Latin/CJK
        hallucination_count = sum(1 for ch in s if ch in GARBLED_HALLUCINATION_CHARS)
        if hallucination_count > 0:
            score -= min(0.40, 0.15 * hallucination_count)

        # Reward recognized industrial keywords
        tokens = re.findall(r"[A-Z0-9]+", upper_s)
        matched_keywords = sum(1 for t in tokens if t in INDUSTRIAL_KEYWORDS)
        if matched_keywords > 0:
            score += min(0.30, 0.15 * matched_keywords)

        # Reward standard key-value format on industrial labels (e.g. "LOT: ABC", "型号：M7605D")
        if re.search(r"^[A-Z0-9\u4e00-\u9fff]{2,12}\s*[:：]\s*\S+", s):
            score += 0.15

        # Reward valid date formats (YYYY-MM-DD, DD/MM/YYYY, YYYY.MM.DD)
        if re.search(r"\b(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})\b", s):
            score += 0.15

        # Reward well-formed serial/code patterns (e.g., WP04635295, ABC-12345, M7605D)
        if re.search(r"\b[A-Z]{1,4}[-]?[0-9]{3,12}[A-Z0-9]*\b", upper_s):
            score += 0.10

        # Penalize strings that are mostly random punctuation or fragmented spaces
        alnum_cjk = sum(
            1 for ch in s if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff")
        )
        ratio_valid = alnum_cjk / float(max(len(s), 1))
        if ratio_valid < 0.45:
            score -= 0.20

        return float(np.clip(score, 0.0, 1.0))
