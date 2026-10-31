"""Compatibility export for the central PatchCore record repository."""

from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordManager,
    PatchCoreTrainRecordRepository,
)

PatchCoreTrainRecordService = PatchCoreTrainRecordRepository

__all__ = [
    "PatchCoreTrainRecordManager",
    "PatchCoreTrainRecordRepository",
    "PatchCoreTrainRecordService",
]
