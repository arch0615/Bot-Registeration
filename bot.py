"""
Registration Bot
────────────────
Reads participants from a CSV file, opens each person's assigned GoLogin
browser profile (with its proxy and fingerprint), navigates to the
registration page, fills the form, and logs the result.

Requirements:
    pip install -r requirements.txt

Usage:
    python bot.py                  # run all rows
    python bot.py --limit 5        # run first 5 rows (dry-run test)
    python bot.py --row 3          # run only row 3 (1-indexed, header excluded)
"""

import asyncio
import csv
import json
import logging
import sys
import time
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import aiohttp
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

import config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    ],
)
log = logging.getLogger(__name__)

GOLOGIN_BASE = f"http://localhost:{config.GOLOGIN_PORT}"


# ── GoLogin helpers ───────────────────────────────────────────────────────────

async def start_profile(session: aiohttp.ClientSession, profile_id: str) -> str | None:
    """Start a GoLogin profile and return the CDP WebSocket URL."""
    url = f"{GOLOGIN_BASE}/browser/{profile_id}/start?return_url=true"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                text = await resp.text()
                log.error("GoLogin start failed (HTTP %s): %s", resp.status, text[:200])
                return None
            data = await resp.json(content_type=None)
            ws_url = data.get("wsUrl") or data.get("ws")
            if not ws_url:
                log.error("GoLogin response missing wsUrl: %s", data)
                return None
            return ws_url
    except aiohttp.ClientConnectorError:
        log.error(
            "Cannot reach GoLogin on port %s — make sure the desktop app is open.",
            config.GOLOGIN_PORT,
        )
        return None
    except Exception as exc:
        log.error("Unexpected error starting profile %s: %s", profile_id, exc)
        return None


async def stop_profile(session: aiohttp.ClientSession, profile_id: str) -> None:
    """Stop a GoLogin profile."""
    url = f"{GOLOGIN_BASE}/browser/{profile_id}/stop"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status not in (200, 204):
                log.warning("GoLogin stop returned HTTP %s for profile %s", resp.status, profile_id)
    except Exception as exc:
        log.warning("Could not stop profile %s: %s", profile_id, exc)


# ── Registration logic ────────────────────────────────────────────────────────

async def register(playwright, ws_url: str, row: dict) -> tuple[bool, str]:
    """
    Connect to the GoLogin browser via CDP, fill the registration form,
    and return (success, message).
    """
    browser = None
    try:
        browser = await playwright.chromium.connect_over_cdp(ws_url)

        # Reuse existing context (GoLogin profile) rather than creating a new one
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()

        page = await context.new_page()

        log.info("  Navigating to %s", config.REGISTRATION_URL)
        await page.goto(config.REGISTRATION_URL, wait_until="domcontentloaded", timeout=30_000)

        # Fill each field defined in FIELD_MAP
        for col, selector in config.FIELD_MAP.items():
            value = str(row.get(col, "")).strip()
            if not value:
                log.warning("  Column '%s' is empty for this row — skipping field.", col)
                continue
            try:
                await page.fill(selector, value)
                log.info("  Filled %-20s → %s", col, selector)
            except Exception as exc:
                return False, f"Could not fill '{col}' ({selector}): {exc}"

        # Submit
        log.info("  Clicking submit: %s", config.SUBMIT_SELECTOR)
        await page.click(config.SUBMIT_SELECTOR)

        # Wait for success indicator
        await page.wait_for_selector(
            config.SUCCESS_SELECTOR,
            timeout=config.SUCCESS_TIMEOUT * 1000,
        )
        return True, "Registered successfully"

    except PWTimeout:
        return False, f"Timed out waiting for success selector '{config.SUCCESS_SELECTOR}'"
    except Exception as exc:
        return False, str(exc)
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


# ── Main loop ─────────────────────────────────────────────────────────────────

async def run(limit: int | None = None, only_row: int | None = None) -> None:
    csv_path = Path(config.CSV_FILE)
    if not csv_path.exists():
        log.error("CSV file not found: %s", csv_path.resolve())
        sys.exit(1)

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        participants = list(reader)

    if not participants:
        log.error("CSV file is empty or has no data rows.")
        sys.exit(1)

    # Apply row/limit filters
    if only_row is not None:
        idx = only_row - 1
        if idx < 0 or idx >= len(participants):
            log.error("--row %s is out of range (CSV has %s data rows).", only_row, len(participants))
            sys.exit(1)
        participants = [participants[idx]]
    elif limit is not None:
        participants = participants[:limit]

    total = len(participants)
    log.info("Starting registration run: %s participant(s)", total)
    log.info("Registration URL: %s", config.REGISTRATION_URL)

    results: list[dict] = []
    ok_count = 0

    async with aiohttp.ClientSession() as session:
        async with async_playwright() as pw:
            for i, row in enumerate(participants, start=1):
                profile_id = str(row.get(config.PROFILE_ID_COLUMN, "")).strip()
                identifier = row.get("email") or row.get("username") or f"row {i}"

                log.info("─" * 60)
                log.info("[%s/%s] %s  (profile: %s)", i, total, identifier, profile_id or "MISSING")

                if not profile_id:
                    msg = f"No '{config.PROFILE_ID_COLUMN}' value in row"
                    log.warning("  SKIP — %s", msg)
                    results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                    continue

                # Start GoLogin profile
                ws_url = await start_profile(session, profile_id)
                if not ws_url:
                    msg = "GoLogin profile failed to start"
                    log.error("  FAIL — %s", msg)
                    results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                    continue

                log.info("  Profile started. CDP: %s", ws_url)
                await asyncio.sleep(config.PROFILE_BOOT_WAIT)

                # Run registration
                success, message = await register(pw, ws_url, row)

                # Stop profile
                await stop_profile(session, profile_id)

                status = "OK" if success else "FAIL"
                if success:
                    ok_count += 1
                    log.info("  ✓ %s", message)
                else:
                    log.error("  ✗ %s", message)

                results.append({**row, "bot_status": status, "bot_message": message})

                if i < total:
                    await asyncio.sleep(config.DELAY_BETWEEN_RUNS)

    # Write results CSV
    out_path = Path(f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        if results:
            fieldnames = list(results[0].keys())
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    log.info("─" * 60)
    log.info("Done.  Success: %s / %s", ok_count, total)
    log.info("Results saved to: %s", out_path.resolve())


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = ArgumentParser(description="Registration bot using GoLogin + Playwright")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows")
    parser.add_argument("--row",   type=int, default=None, help="Only process a single row (1-indexed)")
    args = parser.parse_args()

    if args.limit and args.row:
        print("Use either --limit or --row, not both.")
        sys.exit(1)

    asyncio.run(run(limit=args.limit, only_row=args.row))


if __name__ == "__main__":
    main()
