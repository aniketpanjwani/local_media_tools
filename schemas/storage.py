"""
Atomic file storage with backup and validation.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StorageError(Exception):
    """Base exception for storage operations."""

    pass


class EventStorage:
    """
    Safe storage for event data with atomic writes.

    Uses write-to-temp-then-rename pattern to prevent corruption.
    Keeps one backup of previous version.
    """

    def __init__(self, output_path: Path | str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, data: BaseModel) -> None:
        """
        Save Pydantic model to JSON with atomic write.

        Creates backup of existing file if present.

        Raises:
            StorageError: If write fails.
        """
        # Backup existing file
        if self.output_path.exists():
            backup_path = self.output_path.with_suffix(".json.bak")
            shutil.copy2(self.output_path, backup_path)

        # Write to temp file first (same directory for atomic rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.output_path.parent,
            suffix=".json.tmp",
        )

        try:
            json_str = data.model_dump_json(indent=2)
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(json_str)

            # Validate we can read it back
            with open(temp_path, "r", encoding="utf-8") as f:
                json.load(f)

            # Atomic rename
            shutil.move(temp_path, self.output_path)

        except Exception as e:
            Path(temp_path).unlink(missing_ok=True)
            raise StorageError(f"Failed to save: {e}") from e

    def load(self, model_class: type[T]) -> T:
        """
        Load and validate JSON file into Pydantic model.

        Raises:
            FileNotFoundError: If file doesn't exist.
            StorageError: If JSON is invalid or validation fails.
        """
        if not self.output_path.exists():
            raise FileNotFoundError(f"Not found: {self.output_path}")

        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return model_class.model_validate(data)

        except json.JSONDecodeError as e:
            backup_path = self.output_path.with_suffix(".json.bak")
            if backup_path.exists():
                raise StorageError(
                    f"Corrupted JSON. Backup available at {backup_path}"
                ) from e
            raise StorageError(f"Invalid JSON: {e}") from e

    def exists(self) -> bool:
        """Check if storage file exists."""
        return self.output_path.exists()
