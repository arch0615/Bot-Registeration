"""
Registration Bot — Desktop App
Run with:  python app.py
"""

import asyncio
import csv
import io
import json
import random
import re
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

import aiohttp
import webview
from gologin import GoLogin
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PWTimeout

from steps_config import REGISTRATION_STEPS

SETTINGS_FILE    = Path(__file__).parent / "settings.json"
UI_FILE          = Path(__file__).parent / "ui" / "index.html"
GOLOGIN_API_BASE = "https://api.gologin.com"

DEFAULT_SETTINGS = {
    "registration_url":   "https://www.planetwin365.it/area-personale/registrati/",
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
    "steps":              REGISTRATION_STEPS,
    "profile_mode":       "auto",
}

class _SkipStep(Exception):
    pass

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)


def generate_username(email: str) -> str:
    prefix = email.split("@")[0] if "@" in email else email
    base = re.sub(r'[^a-zA-Z0-9]', '', prefix)
    if len(base) < 4:
        base = base.ljust(4, '0')
    suffix = str(random.randint(100, 9999))
    username = base[:14 - len(suffix)] + suffix
    return username[:14]


PROVINCE_MAP = {
    "AG": "Agrigento", "AL": "Alessandria", "AN": "Ancona", "AO": "Aosta",
    "AP": "Ascoli Piceno", "AQ": "L'Aquila", "AR": "Arezzo", "AT": "Asti",
    "AV": "Avellino", "BA": "Bari", "BG": "Bergamo", "BI": "Biella",
    "BL": "Belluno", "BN": "Benevento", "BO": "Bologna", "BR": "Brindisi",
    "BS": "Brescia", "BT": "Barletta-Andria-Trani", "BZ": "Bolzano",
    "CA": "Cagliari", "CB": "Campobasso", "CE": "Caserta", "CH": "Chieti",
    "CL": "Caltanissetta", "CN": "Cuneo", "CO": "Como", "CR": "Cremona",
    "CS": "Cosenza", "CT": "Catania", "CZ": "Catanzaro", "EN": "Enna",
    "FC": "Forlì-Cesena", "FE": "Ferrara", "FG": "Foggia", "FI": "Firenze",
    "FM": "Fermo", "FR": "Frosinone", "GE": "Genova", "GO": "Gorizia",
    "GR": "Grosseto", "IM": "Imperia", "IS": "Isernia", "KR": "Crotone",
    "LC": "Lecco", "LE": "Lecce", "LI": "Livorno", "LO": "Lodi",
    "LT": "Latina", "LU": "Lucca", "MB": "Monza e Brianza", "MC": "Macerata",
    "ME": "Messina", "MI": "Milano", "MN": "Mantova", "MO": "Modena",
    "MS": "Massa-Carrara", "MT": "Matera", "NA": "Napoli", "NO": "Novara",
    "NU": "Nuoro", "OR": "Oristano", "PA": "Palermo", "PC": "Piacenza",
    "PD": "Padova", "PE": "Pescara", "PG": "Perugia", "PI": "Pisa",
    "PN": "Pordenone", "PO": "Prato", "PR": "Parma", "PT": "Pistoia",
    "PU": "Pesaro e Urbino", "PV": "Pavia", "PZ": "Potenza", "RA": "Ravenna",
    "RC": "Reggio Calabria", "RE": "Reggio Emilia", "RG": "Ragusa",
    "RI": "Rieti", "RM": "Roma", "RN": "Rimini", "RO": "Rovigo",
    "SA": "Salerno", "SI": "Siena", "SO": "Sondrio", "SP": "La Spezia",
    "SR": "Siracusa", "SS": "Sassari", "SU": "Sud Sardegna", "SV": "Savona",
    "TA": "Taranto", "TE": "Teramo", "TN": "Trento", "TO": "Torino",
    "TP": "Trapani", "TR": "Terni", "TS": "Trieste", "TV": "Treviso",
    "UD": "Udine", "VA": "Varese", "VB": "Verbano-Cusio-Ossola",
    "VC": "Vercelli", "VE": "Venezia", "VI": "Vicenza", "VR": "Verona",
    "VT": "Viterbo", "VV": "Vibo Valentia",
}

GENDER_MAP = {"M": "Maschile", "F": "Femminile"}


def format_birthday(raw: str) -> str:
    """Convert DD/MM/YYYY to D/M/YYYY (strip leading zeros)."""
    parts = raw.split("/")
    if len(parts) == 3:
        return f"{int(parts[0])}/{int(parts[1])}/{parts[2]}"
    return raw


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
        s = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE) as f:
                    saved = json.load(f)
                s.update(saved)
            except Exception:
                pass
        s["steps"] = REGISTRATION_STEPS
        if not s.get("registration_url"):
            s["registration_url"] = DEFAULT_SETTINGS["registration_url"]
        return s

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
                    f"{GOLOGIN_API_BASE}/browser/v2",
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
        if event == "log" and data:
            lvl = data.get("lvl", "info").upper()
            msg = data.get("msg", "")
            print(f"[{lvl}] {msg}", flush=True)
        elif event == "row_done" and data:
            print(f"[ROW_DONE] {data.get('label','')} → {data.get('status','')}", flush=True)
        elif event in ("started", "finished", "progress"):
            print(f"[{event.upper()}] {data}", flush=True)
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
        except Exception as e:
            print(f"[FATAL] Bot thread crashed: {e}", flush=True)
            traceback.print_exc()
        finally:
            loop.close()

    async def _bot(self, settings, rows):
        self._running = True
        total     = len(rows)
        ok_count  = 0
        pid_col   = settings.get("profile_id_column", "profile_name")
        field_map = settings.get("field_map", [])
        token     = settings.get("gologin_api_token", "").strip()
        auto_mode = settings.get("profile_mode", "auto") == "auto"

        self._emit("started", {"total": total})

        # Load profiles from GoLogin API
        name_to_id = {}
        profile_list = []
        if token:
            self._emit("log", {"lvl": "info", "msg": "Loading GoLogin profile list…"})
            result = await self._fetch_profiles(token)
            if "profiles" in result:
                for p in result["profiles"]:
                    name_to_id[p["name"]]       = p["id"]
                    name_to_id[p["name"].strip()] = p["id"]
                    profile_list.append(p)
                self._emit("log", {"lvl": "info", "msg": f"  {len(profile_list)} profiles loaded."})
            else:
                self._emit("log", {"lvl": "warn", "msg": f"  Could not load profiles: {result.get('error')}"})

        if auto_mode and not profile_list:
            self._emit("log", {"lvl": "error", "msg": "Auto mode requires profiles — load your GoLogin API token first."})
            self._running = False
            self._emit("finished", {"ok": 0, "total": total, "results": []})
            return

        if auto_mode and len(profile_list) < total:
            self._emit("log", {"lvl": "warn", "msg": f"  ⚠ Only {len(profile_list)} profiles for {total} rows — extra rows will be skipped."})

        async with async_playwright() as pw:
            for i, row in enumerate(rows):
                if self._stop:
                    self._emit("log", {"lvl": "warn", "msg": "Stopped by user."})
                    break

                label = row.get("email") or row.get("username") or row.get("Email") or f"Row {i+1}"

                self._emit("progress", {"i": i, "total": total, "label": label})
                self._emit("log", {"lvl": "info", "msg": f"[{i+1}/{total}] {label}"})

                if auto_mode:
                    if i >= len(profile_list):
                        msg = "No more profiles available"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue
                    pid = profile_list[i]["id"]
                    self._emit("log", {"lvl": "info", "msg": f"  Auto-assigned profile: {profile_list[i]['name']} ({pid[:8]}…)"})
                else:
                    raw_pid = str(row.get(pid_col, "")).strip()

                    if not raw_pid:
                        msg = f"No value in '{pid_col}' column"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue

                    if UUID_RE.match(raw_pid):
                        pid = raw_pid
                    elif raw_pid in name_to_id:
                        pid = name_to_id[raw_pid]
                        self._emit("log", {"lvl": "info", "msg": f"  Resolved '{raw_pid}' → {pid[:8]}…"})
                    else:
                        msg = (
                            f"Profile '{raw_pid}' not found. "
                            "Check your GoLogin API token and profile names."
                        )
                        self._results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                        self._emit("log",      {"lvl": "error", "msg": f"  ✗ {msg}"})
                        self._emit("row_done", {"i": i, "status": "FAIL", "label": label})
                        continue

                self._emit("log", {"lvl": "info", "msg": "  Starting GoLogin profile…"})
                ws = await self._start_profile(token, pid)
                if not ws:
                    msg = "GoLogin profile failed to start"
                    self._results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                    self._emit("log",      {"lvl": "error", "msg": f"  ✗ {msg}"})
                    self._emit("row_done", {"i": i, "status": "FAIL", "label": label})
                    continue

                self._emit("log", {"lvl": "info", "msg": "  Profile started, connecting…"})
                await asyncio.sleep(settings.get("profile_boot_wait", 5))

                ok, msg = await self._fill(pw, ws, row, settings, field_map)
                await self._stop_profile()

                status = "OK" if ok else "FAIL"
                icon   = "✓" if ok else "✗"
                lvl    = "ok" if ok else "error"
                self._results.append({**row, "bot_status": status, "bot_message": msg})
                self._emit("log",      {"lvl": lvl,  "msg": f"  {icon} {msg}"})
                self._emit("row_done", {"i": i, "status": status, "label": label})
                if ok:
                    ok_count += 1

                if i < total - 1 and not self._stop:
                    wait = max(settings.get("delay_between_runs", 2), 5)
                    self._emit("log", {"lvl": "info", "msg": f"  Waiting {wait}s before next profile…"})
                    await asyncio.sleep(wait)

        self._running = False
        self._emit("finished", {
            "ok":      ok_count,
            "total":   total,
            "results": self._results,
        })

    def _create_gl(self, token, pid):
        return GoLogin({
            "token": token,
            "profile_id": pid,
            "extra_params": [
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
            ],
        })

    async def _start_profile(self, token, pid):
        loop = asyncio.get_event_loop()
        try:
            gl = self._create_gl(token, pid)
            ws = await loop.run_in_executor(None, gl.start)
            self._current_gl = gl
            print(f"[DEBUG] gl.start() returned: {repr(ws)}", flush=True)
            ws_str = str(ws) if ws else ""
            if ws_str.startswith("ws://") or ws_str.startswith("wss://"):
                return ws_str
            # Browser not ready yet — poll the debug endpoint
            port = getattr(gl, 'port', None)
            if not port:
                port_match = re.search(r'(\d{4,5})', ws_str)
                if port_match:
                    port = int(port_match.group(1))
            if not port:
                self._emit("log", {"lvl": "error", "msg": "    Cannot determine browser port"})
                return None
            self._emit("log", {"lvl": "info", "msg": f"    Waiting for browser to be ready (port {port})…"})
            for attempt in range(20):
                await asyncio.sleep(2)
                try:
                    async with aiohttp.ClientSession() as s:
                        async with s.get(
                            f"http://127.0.0.1:{port}/json/version",
                            timeout=aiohttp.ClientTimeout(total=3)
                        ) as r:
                            if r.status == 200:
                                data = await r.json(content_type=None)
                                ws = data.get("webSocketDebuggerUrl", "")
                                if ws:
                                    self._emit("log", {"lvl": "info", "msg": f"    Browser ready after {(attempt+1)*2}s"})
                                    return ws
                except Exception:
                    pass
            self._emit("log", {"lvl": "error", "msg": "    Browser never became ready"})
            return None
        except Exception as e:
            self._emit("log", {"lvl": "error", "msg": f"    Start error: {e}"})
            self._current_gl = None
            return None

    async def _stop_profile(self):
        gl = getattr(self, '_current_gl', None)
        if gl:
            print("[INFO] Stopping GoLogin profile…", flush=True)
            loop = asyncio.get_event_loop()
            try:
                await loop.run_in_executor(None, gl.stop)
                print("[INFO] GoLogin profile stopped.", flush=True)
            except Exception as e:
                print(f"[WARN] Error stopping profile: {e}", flush=True)
            self._current_gl = None

    def _resolve_value(self, col, row):
        if col == "__username__":
            email = str(row.get("Email", "") or row.get("email", "")).strip()
            username = generate_username(email)
            row["Username"] = username
            self._emit("update_row", {"email": email, "field": "Username", "value": username})
            return username
        if col == "__province__":
            code = str(row.get("Province", "") or row.get("province", "")).strip().upper()
            return PROVINCE_MAP.get(code, code)
        if col == "__province_of_residence__":
            code = str(row.get("Province of residence", "")).strip().upper()
            return PROVINCE_MAP.get(code, code)
        if col == "__birthday__":
            raw = str(row.get("Birthday", "") or row.get("birthday", "")).strip()
            return format_birthday(raw)
        if col == "__gender__":
            code = str(row.get("Gender", "") or row.get("gender", "")).strip().upper()
            return GENDER_MAP.get(code, code)
        if col == "__house_number__":
            raw = str(row.get("House number", "")).strip()
            return raw.split(" ")[0] if raw else ""
        if col == "__security_question__":
            return "Qual è il tuo secondo nome?"
        if col == "__security_answer__":
            return "abramo"
        if col == "__spending_limit__":
            return "€ 100.000"
        if col == "__document_type__":
            raw = str(row.get("Document type", "")).strip()
            return raw or "Carta d'identità elettronica"
        if col == "__issuing_body__":
            raw = str(row.get("Issuing body", "")).strip()
            return raw or "Comune"
        if col == "__issue_date__":
            raw = str(row.get("Issue date", "") or row.get("issue_date", "")).strip()
            return format_birthday(raw)
        if col == "__expiration_date__":
            raw = str(row.get("Expiration date", "") or row.get("expiration_date", "")).strip()
            return format_birthday(raw)
        return str(row.get(col, "")).strip()

    CURSOR_INJECT_JS = """
    (() => {
        if (document.getElementById('__bot_cursor')) return;
        const style = document.createElement('style');
        style.textContent = '*, *::before, *::after { cursor: none !important; }';
        document.head.appendChild(style);
        const cur = document.createElement('div');
        cur.id = '__bot_cursor';
        cur.style.cssText = `
            position: fixed; z-index: 2147483647; pointer-events: none;
            width: 20px; height: 20px; top: -40px; left: -40px;
            transition: top 0.25s ease-out, left 0.25s ease-out;
        `;
        cur.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="28" viewBox="0 0 17 24">
            <path fill="#fff" stroke="#000" stroke-width="1.2"
                  d="M1 1l0 17.4 4.2-4.2 3.5 7.5 2.7-1.3-3.5-7.5h5.9z"/>
        </svg>`;
        document.body.appendChild(cur);
        document.addEventListener('mousemove', e => {
            cur.style.top = e.clientY + 'px';
            cur.style.left = e.clientX + 'px';
        });
    })();
    """

    async def _inject_cursor(self, page):
        try:
            await page.evaluate(self.CURSOR_INJECT_JS)
        except Exception:
            pass

    async def _move_to_element(self, page, selector):
        """Move the mouse cursor to an element's center with a smooth path."""
        try:
            el = page.locator(selector).first
            await el.scroll_into_view_if_needed()
            box = await el.bounding_box()
            if box:
                tx = box["x"] + box["width"] / 2
                ty = box["y"] + box["height"] / 2
                await page.mouse.move(tx, ty, steps=random.randint(8, 15))
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass

    async def _human_type(self, page, selector, value):
        """Type text character by character with random human-like delays."""
        el = page.locator(selector).first
        await el.click()
        await el.press("Control+a")
        await page.keyboard.press("Backspace")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        for ch in value:
            await page.keyboard.type(ch)
            await asyncio.sleep(random.uniform(0.05, 0.18))
        await page.keyboard.press("Tab")
        await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _random_pause(self, short=False):
        """Random pause to break robotic timing patterns."""
        if short:
            await asyncio.sleep(random.uniform(0.3, 0.8))
        else:
            await asyncio.sleep(random.uniform(0.8, 2.0))

    async def _apply_field(self, page, selector, value, field_type, field_cfg=None):
        """Apply a single field action based on its type."""
        field_type = (field_type or "fill").lower()
        await self._inject_cursor(page)
        if selector:
            try:
                el = page.locator(selector).first
                await el.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass
            await self._move_to_element(page, selector)
        await self._random_pause(short=True)
        if field_type == "fill":
            await self._human_type(page, selector, value)
        elif field_type == "check":
            el = page.locator(selector).first
            label = el.locator("label").first
            should_check = not value or value.lower() in ("true", "1", "yes", "si", "sì")
            try:
                is_checked = await el.evaluate("e => e.classList.contains('mat-mdc-checkbox-checked') || !!e.querySelector('input:checked')")
            except Exception:
                is_checked = False
            if should_check and not is_checked:
                try:
                    await label.click(timeout=3000)
                except Exception:
                    await el.click()
            elif not should_check and is_checked:
                try:
                    await label.click(timeout=3000)
                except Exception:
                    await el.click()
        elif field_type == "radio":
            await page.click(selector)
        elif field_type == "radio_map":
            smap = (field_cfg or {}).get("selector_map", {})
            target = smap.get(value, "")
            if target:
                await page.click(target)
        elif field_type == "select":
            await page.select_option(selector, value)
        elif field_type == "mat_select":
            await page.click(selector)
            await self._random_pause()
            option = page.locator(f"mat-option:has-text('{value}')").first
            try:
                await option.wait_for(state="visible", timeout=3000)
                await self._random_pause(short=True)
                await option.click()
            except Exception:
                options = page.locator("mat-option")
                if await options.count() > 0:
                    await options.first.click()
            await self._random_pause(short=True)
        elif field_type == "click":
            await page.click(selector)
        elif field_type == "click_first":
            el = page.locator(selector).first
            await el.scroll_into_view_if_needed()
            await self._random_pause(short=True)
            await el.click()
        elif field_type == "autocomplete":
            await page.click(selector)
            await page.fill(selector, "")
            for ch in value:
                await page.keyboard.type(ch)
                await asyncio.sleep(random.uniform(0.05, 0.18))
            await self._random_pause()
            dropdown = page.locator("mat-option, [role='listbox'] [role='option'], .autocomplete-suggestion, .MuiAutocomplete-option").first
            try:
                await dropdown.wait_for(state="visible", timeout=3000)
                await self._random_pause(short=True)
                await dropdown.click()
            except Exception:
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
            await self._random_pause(short=True)
        elif field_type == "date":
            parts = value.split("/")
            if len(parts) == 3:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                fake_d = d + 1 if d < 28 else d - 1
                fake = f"{fake_d}/{m}/{y}"
            else:
                fake = "1/1/2000"
            await page.click(selector)
            await self._human_type(page, selector, fake)
            await self._random_pause()
            await self._human_type(page, selector, value)
            await self._random_pause(short=True)
        else:
            await self._human_type(page, selector, value)
        await self._random_pause(short=True)

    async def _fill(self, pw, ws, row, settings, field_map):
        browser = None
        try:
            print(f"[DEBUG] Connecting to CDP: {ws}", flush=True)
            browser = await pw.chromium.connect_over_cdp(ws)
            ctx  = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
            page.on("crash", lambda: print("[WARN] Page crashed!", flush=True))
            browser.on("disconnected", lambda: print("[WARN] Browser disconnected!", flush=True))
            url = settings["registration_url"]
            self._emit("log", {"lvl": "info", "msg": f"    Navigating to {url}"})
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await self._inject_cursor(page)
            await self._random_pause()

            steps = settings.get("steps") or []

            if steps:
                for si, step in enumerate(steps):
                    step_fields = step.get("fields", [])
                    step_submit = step.get("submit_selector", "")
                    wait_sel    = step.get("wait_after", "")
                    optional    = step.get("optional", False)

                    self._emit("log", {"lvl": "info", "msg": f"  Step {si+1}: {step.get('name', f'Page {si+1}')}"})
                    await self._random_pause()
                    await self._inject_cursor(page)

                    try:
                        for m in step_fields:
                            col  = m.get("csv_col", "")
                            sel  = m.get("selector", "")
                            ftype = m.get("type", "fill")

                            if not sel:
                                continue

                            if optional:
                                try:
                                    await page.wait_for_selector(sel, timeout=3000)
                                except PWTimeout:
                                    self._emit("log", {"lvl": "info", "msg": f"    Optional step skipped"})
                                    raise _SkipStep()

                            if ftype in ("radio", "click", "click_first"):
                                self._emit("log", {"lvl": "info", "msg": f"    {ftype}: {sel[:60]}"})
                                await self._apply_field(page, sel, "", ftype)
                            elif ftype == "check":
                                val = self._resolve_value(col, row) if col else ""
                                self._emit("log", {"lvl": "info", "msg": f"    check: {sel[:60]}"})
                                await self._apply_field(page, sel, val, ftype)
                            elif ftype == "radio_map":
                                val = self._resolve_value(col, row) if col else ""
                                if val:
                                    self._emit("log", {"lvl": "info", "msg": f"    radio_map: {val} → {sel[:60]}"})
                                    await self._apply_field(page, sel, val, ftype, m)
                            else:
                                val = self._resolve_value(col, row)
                                if col and sel and val:
                                    self._emit("log", {"lvl": "info", "msg": f"    {ftype}: {col} → {sel[:50]} = {val[:30]}"})
                                    await self._apply_field(page, sel, val, ftype)

                        if step_submit:
                            await self._random_pause()
                            btn = page.locator(step_submit).first
                            try:
                                await btn.scroll_into_view_if_needed(timeout=3000)
                            except Exception:
                                pass
                            # Wait for button to become enabled
                            for _wait in range(15):
                                if await btn.is_enabled():
                                    break
                                self._emit("log", {"lvl": "info", "msg": f"    Waiting for submit button to enable… ({_wait+1})"})
                                await asyncio.sleep(1)
                            else:
                                self._emit("log", {"lvl": "warn", "msg": f"    Submit button still disabled after 15s"})
                            await self._move_to_element(page, step_submit)
                            await btn.click(timeout=15_000)
                            if wait_sel:
                                await page.wait_for_selector(wait_sel, timeout=15_000)
                            else:
                                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                    except _SkipStep:
                        continue

                # Check for registration failure and always go back to page 1
                reg_failed = False
                error_el = page.locator("text=La registrazione non è andata a buon fine")
                try:
                    await error_el.wait_for(state="visible", timeout=5000)
                    reg_failed = True
                    self._emit("log", {"lvl": "warn", "msg": "  Registration failed"})
                except PWTimeout:
                    pass

                self._emit("log", {"lvl": "info", "msg": "  Navigating back to page 1"})
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

                if reg_failed:
                    return False, "Registration failed — returned to page 1"

            else:
                for m in field_map:
                    col = m.get("csv_col", "")
                    sel = m.get("selector", "")
                    ftype = m.get("type", "fill")
                    if ftype in ("radio", "click", "click_first"):
                        if sel:
                            await self._apply_field(page, sel, "", ftype)
                    elif ftype == "check":
                        if sel:
                            val = self._resolve_value(col, row) if col else ""
                            await self._apply_field(page, sel, val, ftype)
                    elif ftype == "radio_map":
                        val = self._resolve_value(col, row) if col else ""
                        if val:
                            await self._apply_field(page, sel, val, ftype, m)
                    else:
                        val = self._resolve_value(col, row)
                        if col and sel and val:
                            await self._apply_field(page, sel, val, ftype)
                fallback_submit = settings.get("submit_selector", "button[type='submit']")
                try:
                    await page.locator(fallback_submit).first.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass
                await page.click(fallback_submit)

            suc = settings.get("success_selector", "")
            if suc:
                await page.wait_for_selector(
                    suc, timeout=settings.get("success_timeout", 15) * 1000
                )
            return True, "Registered successfully"
        except PWTimeout:
            return False, "Timed out waiting for success indicator"
        except Exception as e:
            print(f"[ERROR] _fill exception: {e}", flush=True)
            traceback.print_exc()
            return False, str(e)
        finally:
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
