from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import MAIL_DIR
from .eml_utils import EmlEnvelope, ensure_mail_directories
from .storage import persist_report

logger = logging.getLogger("mail_watcher")


class _NewMailHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, handler: Callable[[Path], asyncio.Future]):
        super().__init__()
        self.loop = loop
        self.handler = handler

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".eml":
            return
        logger.info("New EML detected: %s", path)
        asyncio.run_coroutine_threadsafe(self.handler(path), self.loop)


class MailDirectoryWatcher:
    """Watches the legacy mailserver drop folder and runs the analyzer."""

    def __init__(self, process: Callable[[EmlEnvelope], asyncio.Future], watch_dir: Path = MAIL_DIR):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.process = process
        self.watch_dir = watch_dir
        self.observer = Observer()

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        ensure_mail_directories()
        self.loop = loop
        handler = _NewMailHandler(loop, self._handle_path)
        self.observer.schedule(handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        logger.info("Watching %s for incoming EML files", self.watch_dir)

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join(timeout=2)

    async def _handle_path(self, path: Path) -> None:
        envelope = EmlEnvelope.from_path(path)
        await self.process(envelope)
        path.unlink(missing_ok=True)


def persist_and_return(uuid: str, result) -> None:
    persist_report(uuid, result)
