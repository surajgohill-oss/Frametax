"""
DebugMixin — observability layer injected into every collector.

Responsibilities:
  1. Emit structured error logs to ScraperErrorLog table
  2. Capture screenshots and HTML snapshots on failure (when Playwright page available)
  3. Log verbose debug output to terminal when debug_mode=True
  4. Consult FailureMemory before each operation to skip known-bad patterns
  5. Record new failures and successful fallbacks back to FailureMemory

Usage:
    class StubHubCollector(DebugMixin, BaseCollector):
        ...
        async def _fetch_listings(self, tracked_event):
            # Emit telemetry on any exception:
            async with self.telemetry("fetch_listings", url=url):
                ...
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)


class DebugMixin:
    """
    Mix this into any BaseCollector subclass to get structured observability.

    The mixin expects the collector to have:
      - self.marketplace_slug: str
      - self.settings: Settings
      - self._db_session_factory: callable (set by scheduler before each run)

    debug_mode and slow_mo are set at instantiation time (or via CLI).
    """

    debug_mode: bool = False
    slow_mo_ms: int = 0
    _current_page: Optional["Page"] = None

    # ------------------------------------------------------------------ #
    # Telemetry context manager                                            #
    # ------------------------------------------------------------------ #

    @asynccontextmanager
    async def telemetry(
        self,
        operation: str,
        url: str | None = None,
        selector: str | None = None,
        event_id: str | None = None,
    ):
        """
        Wrap any collector operation. On exception → emit ScraperErrorLog.

        Usage:
            async with self.telemetry("parse_listings", url=url):
                data = response.json()
        """
        try:
            yield
        except Exception as exc:
            error_type = self._classify_error(exc, operation)
            await self._emit_error(
                error_type=error_type,
                operation=operation,
                url=url,
                selector=selector,
                event_id=event_id,
                exception=exc,
            )
            raise

    def _classify_error(self, exc: Exception, operation: str) -> str:
        msg = str(exc).lower()
        if "401" in msg or "403" in msg or "auth" in msg:
            return "auth_failure"
        if "timeout" in msg or "connection" in msg or "network" in msg:
            return "http_failure"
        if "selector" in operation.lower() or "element" in msg:
            return "selector_failure"
        if "json" in msg or "parse" in msg or "key" in msg or "schema" in msg:
            return "parse_error"
        if "empty" in msg or "no listing" in msg:
            return "empty_response"
        return "parse_error"

    async def _emit_error(
        self,
        error_type: str,
        operation: str,
        url: str | None,
        selector: str | None,
        event_id: str | None,
        exception: Exception,
        http_status: int | None = None,
    ):
        screenshot_path = None
        html_path = None

        if self._current_page is not None:
            screenshot_path = await self._capture_screenshot(operation)
            html_path = await self._capture_html(operation)

        raw_sample = str(exception)[:500]

        if self.debug_mode:
            self._debug_log(
                f"[TELEMETRY] {error_type} in {operation}",
                url=url,
                selector=selector,
                error=raw_sample,
                screenshot=screenshot_path,
            )

        # Write to DB if session factory available
        factory = getattr(self, "_db_session_factory", None)
        if factory is not None:
            try:
                from app.models.debug import ScraperErrorLog
                async with factory() as db:
                    log = ScraperErrorLog(
                        marketplace=self.marketplace_slug,
                        event_id=str(event_id) if event_id else None,
                        error_type=error_type,
                        selector=selector,
                        url=url,
                        http_status=http_status,
                        raw_sample=raw_sample,
                        screenshot_path=screenshot_path,
                        html_snapshot_path=html_path,
                        extra={"operation": operation},
                        timestamp=datetime.utcnow(),
                    )
                    db.add(log)
                    await db.commit()
            except Exception as db_err:
                logger.warning("Failed to write error log to DB: %s", db_err)

    # ------------------------------------------------------------------ #
    # Screenshot + HTML snapshot capture                                   #
    # ------------------------------------------------------------------ #

    async def _capture_screenshot(self, label: str) -> str | None:
        if self._current_page is None:
            return None
        try:
            screenshots_dir = Path(
                getattr(self.settings, "screenshots_dir", "/tmp/debug_screenshots")
            )
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = screenshots_dir / f"{self.marketplace_slug}_{label}_{ts}.png"
            await self._current_page.screenshot(path=str(path), full_page=True)
            if self.debug_mode:
                self._debug_log(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            logger.debug("Screenshot capture failed: %s", e)
            return None

    async def _capture_html(self, label: str) -> str | None:
        if self._current_page is None:
            return None
        try:
            html_dir = Path(
                getattr(self.settings, "html_snapshots_dir", "/tmp/debug_html")
            )
            html_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = html_dir / f"{self.marketplace_slug}_{label}_{ts}.html"
            content = await self._current_page.content()
            path.write_text(content, encoding="utf-8")
            if self.debug_mode:
                self._debug_log(f"HTML snapshot saved: {path}")
            return str(path)
        except Exception as e:
            logger.debug("HTML snapshot failed: %s", e)
            return None

    # ------------------------------------------------------------------ #
    # Verbose terminal logging                                             #
    # ------------------------------------------------------------------ #

    def _debug_log(self, msg: str, **kwargs):
        ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        print(f"\033[36m[{ts}][{self.marketplace_slug}] {msg}\033[0m")
        for k, v in kwargs.items():
            if v is not None:
                print(f"  \033[33m{k}:\033[0m {v}")

    async def _debug_pause(self, label: str = ""):
        """Step-through mode: pause and wait for Enter in terminal."""
        if not self.debug_mode:
            return
        print(f"\n\033[35m[STEP] {label} — press Enter to continue...\033[0m", end="", flush=True)
        await asyncio.get_event_loop().run_in_executor(None, input)

    # ------------------------------------------------------------------ #
    # Failure memory consultation                                          #
    # ------------------------------------------------------------------ #

    async def get_known_fallback(
        self, failed_pattern: str, error_type: str
    ) -> str | None:
        """
        Check FailureMemory for a known-good alternative to failed_pattern.
        Returns fallback_pattern if one exists with > 0 successes, else None.
        """
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return None
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == self.marketplace_slug,
                        FailureMemory.failed_pattern == failed_pattern,
                        FailureMemory.fallback_pattern.isnot(None),
                        FailureMemory.fallback_success_count > 0,
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    if self.debug_mode:
                        self._debug_log(
                            f"FailureMemory: using fallback '{record.fallback_pattern}' "
                            f"(succeeded {record.fallback_success_count}x)"
                        )
                    return record.fallback_pattern
        except Exception as e:
            logger.debug("FailureMemory lookup failed: %s", e)
        return None

    async def record_failure(self, failed_pattern: str, error_type: str):
        """Upsert a failure record in FailureMemory."""
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == self.marketplace_slug,
                        FailureMemory.failed_pattern == failed_pattern,
                        FailureMemory.error_type == error_type,
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    record.failure_count += 1
                    record.last_seen = datetime.utcnow()
                    # Auto-skip after 3 consecutive failures with no fallback
                    if record.failure_count >= 3 and not record.fallback_pattern:
                        record.skip_failed = True
                else:
                    record = FailureMemory(
                        marketplace=self.marketplace_slug,
                        error_type=error_type,
                        failed_pattern=failed_pattern,
                        failure_count=1,
                    )
                    db.add(record)
                await db.commit()
        except Exception as e:
            logger.debug("FailureMemory record_failure error: %s", e)

    async def record_fallback_success(self, failed_pattern: str, fallback_pattern: str, error_type: str):
        """Record that a fallback selector succeeded, update FailureMemory."""
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(
                    select(FailureMemory).where(
                        FailureMemory.marketplace == self.marketplace_slug,
                        FailureMemory.failed_pattern == failed_pattern,
                        FailureMemory.error_type == error_type,
                    )
                )
                record = result.scalar_one_or_none()
                if record:
                    record.fallback_pattern = fallback_pattern
                    record.fallback_success_count += 1
                    record.last_success = datetime.utcnow()
                    record.skip_failed = True
                else:
                    record = FailureMemory(
                        marketplace=self.marketplace_slug,
                        error_type=error_type,
                        failed_pattern=failed_pattern,
                        fallback_pattern=fallback_pattern,
                        fallback_success_count=1,
                    )
                    db.add(record)
                await db.commit()
                if self.debug_mode:
                    self._debug_log(
                        f"FailureMemory: recorded fallback success "
                        f"'{failed_pattern}' → '{fallback_pattern}'"
                    )
        except Exception as e:
            logger.debug("FailureMemory record_fallback_success error: %s", e)

    async def should_skip_pattern(self, pattern: str, error_type: str) -> bool:
        """Returns True if this pattern is flagged skip_failed=True in FailureMemory."""
        factory = getattr(self, "_db_session_factory", None)
        if factory is None:
            return False
        try:
            from sqlalchemy import select
            from app.models.debug import FailureMemory
            async with factory() as db:
                result = await db.execute(
                    select(FailureMemory.skip_failed).where(
                        FailureMemory.marketplace == self.marketplace_slug,
                        FailureMemory.failed_pattern == pattern,
                        FailureMemory.error_type == error_type,
                        FailureMemory.skip_failed == True,
                    )
                )
                return result.scalar_one_or_none() is not None
        except Exception:
            return False
