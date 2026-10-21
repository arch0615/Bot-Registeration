"""
Registration Bot — Desktop App
Run with:  python app.py
"""

import asyncio
import csv
import io
import json
import re
import sys
import threading
from datetime import datetime
from pathlib import Path

import aiohttp
import webview
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PWTimeout

SETTINGS_FILE    = Path(__file__).parent / "settings.json"
UI_FILE          = Path(__file__).parent / "ui" / "index.html"
GOLOGIN_API_BASE = "https://api.gologin.com"

DEFAULT_SETTINGS = {
    "registration_url":   "",
    "profile_id_column":  "profile_name",
    "field_map":          [],
    "submit_selector":    "button[type='submit']",
    "success_selector":   "",
    "success_timeout":    15,
    "profile_boot_wait":  3,
    "delay_between_runs": 2,
    "gologin_port":       36912,
    "gologin_api_token":  "",
    "last_csv":           "",
    "steps":              [],
}

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)


class API:
    def __init__(self):
        self._window   = None
        self._running  = False
        self._stop     = False
        self._results  = []
        self._headers  = []
        self._rows     = []

    # ── Settings ─────────────────────────────────────────────────────
    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE) as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)

    def save_settings(self, data):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            return {"error": str(e)}

    # ── CSV ──────────────────────────────────────────────────────────
    def pick_csv_file(self):
        paths = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("CSV Files (*.csv)", "All Files (*.*)")
        )
        if paths and paths[0]:
            return self._load_path(paths[0])
        return None

    def load_csv_from_path(self, path):
        if path and Path(path).exists():
            return self._load_path(path)
        return None

    def load_csv_from_text(self, text, filename=""):
        try:
            reader  = csv.DictReader(io.StringIO(text))
            headers = list(reader.fieldnames or [])
            rows    = [dict(r) for r in reader]
            self._headers = headers
            self._rows    = rows
            return {"headers": headers, "rows": rows, "path": filename}
        except Exception as e:
            return {"error": str(e)}

    def _load_path(self, path):
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader  = csv.DictReader(f)
                headers = list(reader.fieldnames or [])
                rows    = [dict(r) for r in reader]
            self._headers = headers
            self._rows    = rows
            s = self.load_settings()
            s["last_csv"] = str(path)
            self.save_settings(s)
            return {"headers": headers, "rows": rows, "path": str(path)}
        except Exception as e:
            return {"error": str(e)}

    def update_table(self, headers, rows):
        self._headers = list(headers)
        self._rows    = [dict(r) for r in rows]
        return True

    def save_csv_dialog(self, headers, rows):
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="participants.csv",
            file_types=("CSV Files (*.csv)", "All Files (*.*)")
        )
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            return path
        except Exception as e:
            return {"error": str(e)}

    # ── GoLogin profiles ──────────────────────────────────────────────
    def load_gologin_profiles(self, token):
        """Fetch all profiles from GoLogin cloud API."""
        if not token or not token.strip():
            return {"error": "No API token provided."}
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._fetch_profiles(token.strip()))
        finally:
            loop.close()

    async def _fetch_profiles(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(
                    f"{GOLOGIN_API_BASE}/browser",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as r:
                    if r.status == 401:
                        return {"error": "Invalid API token — check GoLogin → Settings → API."}
                    if r.status != 200:
                        return {"error": f"GoLogin API error: HTTP {r.status}"}
                    data = await r.json(content_type=None)
                    # API may return {profiles: [...]} or a plain list
                    if isinstance(data, list):
                        profiles = data
                    else:
                        profiles = (
                            data.get("profiles") or
                            data.get("items")    or
                            data.get("data")     or []
                        )
                    # Normalise fields
                    out = []
                    for p in profiles:
                        proxy = p.get("proxy") or {}
                        proxy_str = ""
                        if proxy.get("host"):
                            proxy_str = f"{proxy.get('mode','http')}://{proxy['host']}:{proxy.get('port','')}"
                        out.append({
                            "id":    p.get("id", ""),
                            "name":  p.get("name", ""),
                            "notes": p.get("notes", ""),
                            "proxy": proxy_str,
                        })
                    return {"profiles": out}
        except aiohttp.ClientConnectorError:
            return {"error": "No internet connection — cannot reach GoLogin API."}
        except Exception as e:
            return {"error": str(e)}

    # ── Bot ──────────────────────────────────────────────────────────
    def start_bot(self, settings):
        if self._running:
            return {"ok": False, "error": "Bot is already running."}
        if not self._rows:
            return {"ok": False, "error": "No participant data loaded."}
        if not settings.get("registration_url", "").strip():
            return {"ok": False, "error": "Registration URL is not configured."}

        self._stop    = False
        self._results = []
        threading.Thread(
            target=self._thread_run,
            args=(settings, list(self._rows)),
            daemon=True
        ).start()
        return {"ok": True}

    def stop_bot(self):
        self._stop = True
        return True

    def export_results_dialog(self):
        if not self._results:
            return None
        fname  = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=fname,
            file_types=("CSV Files (*.csv)", "All Files (*.*)")
        )
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(self._results[0].keys()))
                writer.writeheader()
                writer.writerows(self._results)
            return path
        except Exception as e:
            return {"error": str(e)}

    # ── Internals ─────────────────────────────────────────────────────
    def _emit(self, event, data=None):
        payload = json.dumps({"event": event, "data": data}, default=str)
        escaped = (payload
                   .replace("\\", "\\\\")
                   .replace("`",  "\\`")
                   .replace("${", "\\${"))
        self._window.evaluate_js(f"window.__botEvent(`{escaped}`)")

    def _thread_run(self, settings, rows):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._bot(settings, rows))
        finally:
            loop.close()

    async def _bot(self, settings, rows):
        self._running = True
        total     = len(rows)
        ok_count  = 0
        port      = settings.get("gologin_port", 36912)
        base      = f"http://localhost:{port}"
        pid_col   = settings.get("profile_id_column", "profile_name")
        field_map = settings.get("field_map", [])
        token     = settings.get("gologin_api_token", "").strip()

        self._emit("started", {"total": total})

        # Build name→UUID map if API token is available
        name_to_id = {}
        if token:
            self._emit("log", {"lvl": "info", "msg": "Loading GoLogin profile list…"})
            result = await self._fetch_profiles(token)
            if "profiles" in result:
                for p in result["profiles"]:
                    name_to_id[p["name"]]       = p["id"]
                    name_to_id[p["name"].strip()] = p["id"]
                self._emit("log", {"lvl": "info", "msg": f"  {len(name_to_id)//2} profiles loaded."})
            else:
                self._emit("log", {"lvl": "warn", "msg": f"  Could not load profiles: {result.get('error')}"})

        async with aiohttp.ClientSession() as sess:
            async with async_playwright() as pw:
                for i, row in enumerate(rows):
                    if self._stop:
                        self._emit("log", {"lvl": "warn", "msg": "Stopped by user."})
                        break

                    raw_pid = str(row.get(pid_col, "")).strip()
                    label   = row.get("email") or row.get("username") or f"Row {i+1}"

                    self._emit("progress", {"i": i, "total": total, "label": label})
                    self._emit("log", {"lvl": "info", "msg": f"[{i+1}/{total}] {label}"})

                    if not raw_pid:
                        msg = f"No value in '{pid_col}' column"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue

                    # Resolve name → UUID if needed
                    if UUID_RE.match(raw_pid):
                        pid = raw_pid
                    elif raw_pid in name_to_id:
                        pid = name_to_id[raw_pid]
                        self._emit("log", {"lvl": "info", "msg": f"  Resolved '{raw_pid}' → {pid[:8]}…"})
                    else:
                        msg = (
                            f"Profile '{raw_pid}' not found. "
                            "Add your GoLogin API token in Configuration to resolve names."
                        )
                        self._results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                        self._emit("log",      {"lvl": "error", "msg": f"  ✗ {msg}"})
                        self._emit("row_done", {"i": i, "status": "FAIL", "label": label})
                        continue

                    ws = await self._start_profile(sess, base, pid)
                    if not ws:
                        msg = "GoLogin profile failed to start"
                        self._results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                        self._emit("log",      {"lvl": "error", "msg": f"  ✗ {msg}"})
                        self._emit("row_done", {"i": i, "status": "FAIL", "label": label})
                        continue

                    self._emit("log", {"lvl": "info", "msg": "  Profile started, connecting…"})
                    await asyncio.sleep(settings.get("profile_boot_wait", 3))

                    ok, msg = await self._fill(pw, ws, row, settings, field_map)
                    await self._stop_profile(sess, base, pid)

                    status = "OK" if ok else "FAIL"
                    icon   = "✓" if ok else "✗"
                    lvl    = "ok" if ok else "error"
                    self._results.append({**row, "bot_status": status, "bot_message": msg})
                    self._emit("log",      {"lvl": lvl,  "msg": f"  {icon} {msg}"})
                    self._emit("row_done", {"i": i, "status": status, "label": label})
                    if ok:
                        ok_count += 1

                    if i < total - 1 and not self._stop:
                        await asyncio.sleep(settings.get("delay_between_runs", 2))

        self._running = False
        self._emit("finished", {
            "ok":      ok_count,
            "total":   total,
            "results": self._results,
        })

    async def _start_profile(self, sess, base, pid):
        try:
            async with sess.get(
                f"{base}/browser/{pid}/start?return_url=true",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as r:
                if r.status != 200:
                    return None
                d = await r.json(content_type=None)
                return d.get("wsUrl") or d.get("ws")
        except Exception:
            return None

    async def _stop_profile(self, sess, base, pid):
        try:
            async with sess.get(
                f"{base}/browser/{pid}/stop",
                timeout=aiohttp.ClientTimeout(total=15)
            ):
                pass
        except Exception:
            pass

    async def _apply_field(self, page, selector, value, field_type):
        """Apply a single field action based on its type."""
        field_type = (field_type or "fill").lower()
        if field_type == "fill":
            await page.fill(selector, value)
        elif field_type == "check":
            if value.lower() in ("true", "1", "yes", "si", "sì"):
                await page.check(selector)
            else:
                await page.uncheck(selector)
        elif field_type == "radio":
            await page.click(selector)
        elif field_type == "select":
            await page.select_option(selector, value)
        elif field_type == "click":
            await page.click(selector)
        else:
            await page.fill(selector, value)

    async def _fill(self, pw, ws, row, settings, field_map):
        browser = None
        try:
            browser = await pw.chromium.connect_over_cdp(ws)
            ctx  = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            await page.goto(
                settings["registration_url"],
                wait_until="domcontentloaded",
                timeout=30_000
            )

            steps = settings.get("steps") or []

            if steps:
                for si, step in enumerate(steps):
                    step_fields = step.get("fields", [])
                    step_submit = step.get("submit_selector", "")
                    wait_sel    = step.get("wait_after", "")

                    self._emit("log", {"lvl": "info", "msg": f"  Step {si+1}: {step.get('name', f'Page {si+1}')}"})

                    for m in step_fields:
                        col  = m.get("csv_col", "")
                        sel  = m.get("selector", "")
                        ftype = m.get("type", "fill")

                        if ftype in ("radio", "click"):
                            if sel:
                                await self._apply_field(page, sel, "", ftype)
                        else:
                            val = str(row.get(col, "")).strip()
                            if col and sel and val:
                                await self._apply_field(page, sel, val, ftype)

                    if step_submit:
                        await page.click(step_submit)
                        if wait_sel:
                            await page.wait_for_selector(wait_sel, timeout=15_000)
                        else:
                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)

            else:
                for m in field_map:
                    col = m.get("csv_col", "")
                    sel = m.get("selector", "")
                    ftype = m.get("type", "fill")
                    val = str(row.get(col, "")).strip()
                    if ftype in ("radio", "click"):
                        if sel:
                            await self._apply_field(page, sel, "", ftype)
                    elif col and sel and val:
                        await self._apply_field(page, sel, val, ftype)
                await page.click(settings.get("submit_selector", "button[type='submit']"))

            suc = settings.get("success_selector", "")
            if suc:
                await page.wait_for_selector(
                    suc, timeout=settings.get("success_timeout", 15) * 1000
                )
            return True, "Registered successfully"
        except PWTimeout:
            return False, "Timed out waiting for success indicator"
        except Exception as e:
            return False, str(e)
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass


# ── Launch ────────────────────────────────────────────────────────────────────
api    = API()
window = webview.create_window(
    title    = "Registration Bot",
    url      = str(UI_FILE),
    js_api   = api,
    width    = 1200,
    height   = 760,
    min_size = (900, 600),
)
api._window = window

if __name__ == "__main__":
    webview.start()
