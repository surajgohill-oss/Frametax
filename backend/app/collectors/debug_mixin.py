import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)


class DebugMixin:
    debug_mode: bool = False
    slow_mo_ms: int = 0
    _current_page: Optional["Page"] = None

    @asynccontextmanager
    async def telemetry(self, operation: str, url: str | None = None, selector: str | None = None, event_id: str | None = None):
        try:
            yield
        except Exception as exc:
            error_type = self._classify_error(exc, operation)
            await self._emit_error(error_type=error_type, operation=operation, url=url, selector=selector, event_id=event_id, exception=exc)
            raise

    def _classify_error(self, exc: Exception, operation: str) -> str:
        msg = str(exc).lower()
        if "401" in msg or "403" in msg or "auth" in msg: return "auth_failure"
        if "timeout" in msg or "connection" in msg or "network" in msg: return "http_failure"
        if "selector" in operation.lower() or "element" in msg: return "selector_failure"
        if "json" in msg or "parse" in msg or "key" in msg: return "parse_error"
        if "empty" in msg or "no listing" in msg: return "empty_response"
        return "parse_error"

    async def _emit_error(self, error_type, operation, url, selector, event_id, exception, http_status=None):
        screenshot_path = await self._capture_screenshot(operation) if self._current_page else None
        html_path = await self._capture_html(operation) if self._current_page else None
        raw_sample = str(exception)[:500]
        if self.debug_mode:
            self._debug_log(f"[TELEMETRY] {error_type} in {operation}", url=url, error=raw_sample)
        factory = getattr(self, "_db_session_factory", None)
        if factory is not None:
            try:
                from app.models.debug import ScraperErrorLog
                async with factory() as db:
                    db.add(ScraperErrorLog(
                        marketplace=self.marketplace_slug, event_id=str(event_id) if event_id else None,
                        error_type=error_type, selector=selector, url=url, http_status=http_status,
                        raw_sample=raw_sample, screenshot_path=screenshot_path,
                        html_snapshot_path=html_path, extra={"operation": operation}, timestamp=datetime.utcnow(),
                    ))
                    await db.commit()
            except Exception as db_err:
                logger.warning("Failed to write error log to DB: %s", db_err)

    async def _capture_screenshot(self, label: str) -> str | None:
        if self._current_page is None: return None
        try:
            d = Path(getattr(self.settings, "screenshots_dir", "/tmp/debug_screenshots"))
            d.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = d / f"{self.marketplace_slug}_{label}_{ts}.png"
            await self._current_page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception: return None

    async def _capture_html(self, label: str) -> str | None:
        if self._current_page is None: return None
        try:
            d = Path(getattr(self.settings, "html_snapshots_dir", "/tmp/debug_html"))
            d.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = d / f"{self.marketplace_slug}_{label}_{ts}.html"
            path.write_text(await self._current_page.content(), encoding="utf-8")
            return str(path)
        except Exception: return None

    def _debug_log(self, msg: str, **kwargs):
        ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        print(f"\033[36m[{ts}][{self.marketplace_slug}] {msg}\033[0m")
        for k, v in kwargs.items():
            if v is not None: print(f"  \033[33m{k}:\033[0m {v}")

    async def _debug_pause(self, label: str = ""):
        if not self.debug_mode: return
        print(f"\n\033[35m[STEP] {label} — press Enter to continue...\033[0m", end="", flush=True)
        await asyncio.get_event_loop().run_in_executor(None, input)

    async def get_known_fallback(self, failed_pattern: str, error_type: str) -> str | None:
        factory = getattr(self, "_db_session_factory", None)
        if factory is None: return None
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(select(FailureMemory).where(
                    FailureMemory.marketplace == self.marketplace_slug,
                    FailureMemory.failed_pattern == failed_pattern,
                    FailureMemory.fallback_pattern.isnot(None),
                    FailureMemory.fallback_success_count > 0,
                ))
                record = result.scalar_one_or_none()
                return record.fallback_pattern if record else None
        except Exception: return None

    async def record_failure(self, failed_pattern: str, error_type: str):
        factory = getattr(self, "_db_session_factory", None)
        if factory is None: return
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(select(FailureMemory).where(
                    FailureMemory.marketplace == self.marketplace_slug,
                    FailureMemory.failed_pattern == failed_pattern,
                    FailureMemory.error_type == error_type,
                ))
                record = result.scalar_one_or_none()
                if record:
                    record.failure_count += 1
                    record.last_seen = datetime.utcnow()
                    if record.failure_count >= 3 and not record.fallback_pattern:
                        record.skip_failed = True
                else:
                    record = FailureMemory(marketplace=self.marketplace_slug, error_type=error_type, failed_pattern=failed_pattern, failure_count=1)
                    db.add(record)
                await db.commit()
        except Exception as e: logger.debug("FailureMemory record_failure error: %s", e)

    async def record_fallback_success(self, failed_pattern: str, fallback_pattern: str, error_type: str):
        factory = getattr(self, "_db_session_factory", None)
        if factory is None: return
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(select(FailureMemory).where(
                    FailureMemory.marketplace == self.marketplace_slug,
                    FailureMemory.failed_pattern == failed_pattern,
                    FailureMemory.error_type == error_type,
                ))
                record = result.scalar_one_or_none()
                if record:
                    record.fallback_pattern = fallback_pattern
                    record.fallback_success_count += 1
                    record.last_success = datetime.utcnow()
                    record.skip_failed = True
                else:
                    record = FailureMemory(marketplace=self.marketplace_slug, error_type=error_type, failed_pattern=failed_pattern, fallback_pattern=fallback_pattern, fallback_success_count=1)
                    db.add(record)
                await db.commit()
        except Exception as e: logger.debug("FailureMemory record_fallback_success error: %s", e)

    async def should_skip_pattern(self, pattern: str, error_type: str) -> bool:
        factory = getattr(self, "_db_session_factory", None)
        if factory is None: return False
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(select(FailureMemory.skip_failed).where(
                    FailureMemory.marketplace == self.marketplace_slug,
                    FailureMemory.failed_pattern == pattern,
                    FailureMemory.error_type == error_type,
                    FailureMemory.skip_failed == True,
                ))
                return result.scalar_one_or_none() is not None
        except Exception: return False
