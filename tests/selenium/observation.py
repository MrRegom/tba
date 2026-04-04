"""Helpers para registrar evidencia y observaciones durante pruebas Selenium."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os
import re


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return text or "step"


@dataclass
class VisualObserver:
    """Captura screenshots y genera un registro legible de cada paso."""

    driver: object
    test_name: str
    enabled: bool = True
    base_dir: Path | None = None
    records: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        artifacts_dir = self.base_dir or Path(
            os.environ.get("SELENIUM_ARTIFACTS_DIR", "tests/selenium/artifacts")
        )
        self.output_dir = artifacts_dir / _slugify(self.test_name)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_dir / "observaciones.md"
        if self.enabled:
            self.log_path.write_text(
                f"# Observaciones UI\n\nPrueba: `{self.test_name}`\n\n",
                encoding="utf-8",
            )

    def note(self, title: str, observation: str = "") -> str | None:
        if not self.enabled:
            return None

        step_number = len(self.records) + 1
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{step_number:02d}-{timestamp}-{_slugify(title)}.png"
        screenshot_path = self.output_dir / filename
        self.driver.save_screenshot(str(screenshot_path))

        current_url = getattr(self.driver, "current_url", "")
        title_text = getattr(self.driver, "title", "")
        entry = {
            "step": str(step_number),
            "title": title,
            "observation": observation,
            "screenshot": filename,
            "url": current_url,
            "page_title": title_text,
        }
        self.records.append(entry)

        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"## Paso {step_number}: {title}\n")
            fh.write(f"- URL: `{current_url}`\n")
            fh.write(f"- Titulo: `{title_text}`\n")
            fh.write(f"- Screenshot: `{filename}`\n")
            if observation:
                fh.write(f"- Observacion: {observation}\n")
            fh.write("\n")

        return str(screenshot_path)
