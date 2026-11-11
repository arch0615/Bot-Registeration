"""
Registration Bot — Desktop App
Run with:  python app.py
"""

import asyncio
import csv
import io
import json
import os
import random
import re
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path


# ── Packaging-aware paths ─────────────────────────────────────────────────────
# When frozen by PyInstaller, bundled read-only resources (ui/, etc.) live under
# sys._MEIPASS. Writable user state (settings.json, history, IDs/, CSV exports,
# logs) lives per-user under %LOCALAPPDATA%\R-Bot\UserData so the install dir
# can stay read-only without admin rights.
_IS_FROZEN = bool(getattr(sys, "frozen", False))
if _IS_FROZEN:
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    EXE_DIR    = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).parent
    EXE_DIR    = Path(__file__).parent

_local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
USER_DATA_DIR = Path(_local_appdata) / "R-Bot" / "UserData"
try:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (USER_DATA_DIR / "IDs").mkdir(exist_ok=True)
    (USER_DATA_DIR / "logs").mkdir(exist_ok=True)
except Exception:
    # Fall back to the exe folder if LOCALAPPDATA is unwritable
    USER_DATA_DIR = EXE_DIR / "UserData"
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Point Playwright at the chromium bundled next to the exe (the Inno Setup
# installer ships it here). If the bundled folder is missing we leave the env
# var alone so a dev run still resolves to ~/AppData/Local/ms-playwright/.
_bundled_browsers = EXE_DIR / "playwright-browsers"
if _bundled_browsers.is_dir() and not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_bundled_browsers)

import aiohttp
import webview
from gologin import GoLogin
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PWTimeout

from sites import SITES

SETTINGS_FILE    = USER_DATA_DIR / "settings.json"
HISTORY_FILE     = USER_DATA_DIR / "run_history.json"
UI_FILE          = BUNDLE_DIR / "ui" / "index.html"
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
    "profile_mode":       "auto",
    "selected_site":      "1",
    "bonus_selection":    "Casino",
    "excluded_profile_ids": [],
    "profile_site_usage":  {},
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
        self._window      = None
        self._running     = False
        self._stop        = False
        self._results     = []
        self._headers     = []
        self._rows        = []
        self._bot_thread  = None
        self._bot_loop    = None

    # ── Settings ─────────────────────────────────────────────────────
    def get_sites(self):
        return {k: {"name": v["name"], "url": v["url"]} for k, v in SITES.items()}

    def load_settings(self):
        s = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE) as f:
                    saved = json.load(f)
                s.update(saved)
            except Exception:
                pass
        site_id = s.get("selected_site", "1")
        site = SITES.get(site_id, SITES["1"])
        s["steps"] = site["steps"]
        s["registration_url"] = site["url"]
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

    def pick_id_folder(self):
        paths = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if paths and paths[0]:
            s = self.load_settings()
            s["id_folder"] = paths[0]
            self.save_settings(s)
            return {"path": paths[0]}
        return None

    def load_csv_from_path(self, path):
        if not path:
            return None
        if not Path(path).exists():
            return {"error": f"CSV not found: {path}"}
        return self._load_path(path)

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

    # Common CSV encodings exported by Excel / Italian Windows. Tried in order;
    # latin-1 is the final fallback because it is single-byte and never raises.
    _CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

    def _load_path(self, path):
        last_err = None
        for enc in self._CSV_ENCODINGS:
            try:
                with open(path, newline="", encoding=enc) as f:
                    reader  = csv.DictReader(f)
                    headers = list(reader.fieldnames or [])
                    rows    = [dict(r) for r in reader]
                self._headers = headers
                self._rows    = rows
                s = self.load_settings()
                s["last_csv"] = str(path)
                self.save_settings(s)
                return {"headers": headers, "rows": rows, "path": str(path), "encoding": enc}
            except UnicodeDecodeError as e:
                last_err = f"{enc}: {e}"
                continue
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Could not decode CSV with any known encoding. Last error — {last_err}"}

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

    def set_profile_excluded(self, profile_id, excluded):
        """Mark/unmark a GoLogin profile so the bot will skip it during runs."""
        if not profile_id:
            return {"error": "No profile ID provided."}
        s = self.load_settings()
        current = list(s.get("excluded_profile_ids", []))
        if excluded and profile_id not in current:
            current.append(profile_id)
        elif not excluded and profile_id in current:
            current = [p for p in current if p != profile_id]
        s["excluded_profile_ids"] = current
        self.save_settings(s)
        return {"ok": True, "excluded_profile_ids": current}

    def _mark_profile_used(self, profile_id, site_id):
        """Record that `profile_id` successfully registered on `site_id`."""
        if not profile_id or not site_id:
            return
        s = self.load_settings()
        usage = dict(s.get("profile_site_usage", {}) or {})
        sites = list(usage.get(profile_id, []))
        sid = str(site_id)
        if sid not in sites:
            sites.append(sid)
        usage[profile_id] = sites
        s["profile_site_usage"] = usage
        self.save_settings(s)

    def clear_profile_usage(self, profile_id):
        """Reset a profile's per-site registration history so it can be reused."""
        if not profile_id:
            return {"error": "No profile ID provided."}
        s = self.load_settings()
        usage = dict(s.get("profile_site_usage", {}) or {})
        usage.pop(profile_id, None)
        s["profile_site_usage"] = usage
        self.save_settings(s)
        return {"ok": True}

    async def _fetch_profiles(self, token):
        """
        Fetch ALL profiles from GoLogin. The /browser/v2 endpoint paginates
        with a server-side default page size of 30 — we must walk the pages,
        otherwise the UI only ever shows the first 30 profiles regardless of
        how many the account owns.
        """
        headers = {"Authorization": f"Bearer {token}"}
        PAGE_SIZE = 100       # GoLogin accepts up to a few hundred; 100 is safe.
        MAX_PAGES = 200       # Hard safety cap → up to 20 000 profiles.
        out = []
        s = self.load_settings()
        excluded = set(s.get("excluded_profile_ids", []))
        usage = s.get("profile_site_usage", {}) or {}
        try:
            async with aiohttp.ClientSession() as sess:
                total_expected = None
                for page in range(1, MAX_PAGES + 1):
                    params = {"page": page, "limit": PAGE_SIZE}
                    async with sess.get(
                        f"{GOLOGIN_API_BASE}/browser/v2",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as r:
                        if r.status == 401:
                            return {"error": "Invalid API token - check GoLogin > Settings > API."}
                        if r.status != 200:
                            return {"error": f"GoLogin API error: HTTP {r.status}"}
                        data = await r.json(content_type=None)

                    # Response shape: either a raw list, or a dict wrapping it.
                    if isinstance(data, list):
                        profiles = data
                    else:
                        profiles = (
                            data.get("profiles") or
                            data.get("items")    or
                            data.get("data")     or []
                        )
                        # Capture total count on first page if present
                        if total_expected is None:
                            for k in ("allProfilesCount", "totalProfiles",
                                      "profilesCount", "total", "count"):
                                if isinstance(data.get(k), int):
                                    total_expected = data[k]
                                    break

                    for p in profiles:
                        proxy = p.get("proxy") or {}
                        proxy_str = ""
                        if proxy.get("host"):
                            proxy_str = f"{proxy.get('mode','http')}://{proxy['host']}:{proxy.get('port','')}"
                        pid = p.get("id", "")
                        out.append({
                            "id":         pid,
                            "name":       p.get("name", ""),
                            "notes":      p.get("notes", ""),
                            "proxy":      proxy_str,
                            "excluded":   pid in excluded,
                            "used_sites": list(usage.get(pid, [])),
                        })

                    # Stop when the page is short (last page) or we've hit the total.
                    if len(profiles) < PAGE_SIZE:
                        break
                    if total_expected is not None and len(out) >= total_expected:
                        break

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

        site_id = settings.get("selected_site", "1")
        site = SITES.get(site_id)
        if not site:
            return {"ok": False, "error": f"Unknown site: #{site_id}"}
        settings["registration_url"] = site["url"]
        settings["steps"] = site["steps"]
        self._cur_settings = settings

        if not settings.get("registration_url", "").strip():
            return {"ok": False, "error": f"Website #{site_id} has no registration URL configured yet."}

        self._stop    = False
        self._results = []
        t = threading.Thread(
            target=self._thread_run,
            args=(settings, list(self._rows)),
            daemon=True
        )
        self._bot_thread = t
        t.start()
        return {"ok": True}

    def stop_bot(self):
        self._stop = True
        try:
            self._stop_profile_sync()
        except Exception:
            pass
        if self._bot_loop and self._bot_loop.is_running():
            for task in asyncio.all_tasks(self._bot_loop):
                self._bot_loop.call_soon_threadsafe(task.cancel)
        self._running = False
        return True

    def _stop_profile_sync(self):
        gl = getattr(self, "_current_gl", None)
        if gl:
            try:
                gl.stop()
            except Exception:
                pass
            self._current_gl = None

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

    # ── Dashboard / History ──────────────────────────────────────────
    def get_run_history(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_run_record(self, site_id, ok, total, results):
        history = self.get_run_history()
        history.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "site": site_id,
            "site_name": SITES.get(site_id, {}).get("name", f"#{site_id}"),
            "ok": ok,
            "total": total,
            "results": [{"email": r.get("email", ""), "status": r.get("bot_status", "")} for r in results],
        })
        history = history[:200]
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def clear_run_history(self):
        try:
            if HISTORY_FILE.exists():
                HISTORY_FILE.unlink()
            return True
        except Exception as e:
            return {"error": str(e)}

    # ── Internals ─────────────────────────────────────────────────────
    def _emit(self, event, data=None):
        if event == "log" and data:
            lvl = data.get("lvl", "info").upper()
            msg = data.get("msg", "")
            print(f"[{lvl}] {msg}".encode("ascii", "replace").decode(), flush=True)
        elif event == "row_done" and data:
            print(f"[ROW_DONE] {data.get('label','')} -> {data.get('status','')}", flush=True)
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
        self._bot_loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._bot(settings, rows))
        except asyncio.CancelledError:
            print("[INFO] Bot force-stopped by user.", flush=True)
        except Exception as e:
            print(f"[FATAL] Bot thread crashed: {e}", flush=True)
            traceback.print_exc()
        finally:
            self._bot_loop = None
            self._running = False
            loop.close()

    async def _bot(self, settings, rows):
        self._running = True
        self._current_settings = settings
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
        excluded_ids = set(settings.get("excluded_profile_ids", []))
        site_id = str(settings.get("selected_site", "1"))
        usage_map = settings.get("profile_site_usage", {}) or {}
        already_used_ids = {pid for pid, sites in usage_map.items() if site_id in (sites or [])}
        if token:
            self._emit("log", {"lvl": "info", "msg": "Loading GoLogin profile list…"})
            result = await self._fetch_profiles(token)
            if "profiles" in result:
                skipped_excluded = 0
                skipped_used = 0
                for p in result["profiles"]:
                    if p["id"] in excluded_ids:
                        skipped_excluded += 1
                        continue
                    if p["id"] in already_used_ids:
                        skipped_used += 1
                        continue
                    name_to_id[p["name"]]       = p["id"]
                    name_to_id[p["name"].strip()] = p["id"]
                    profile_list.append(p)
                self._emit("log", {"lvl": "info", "msg": f"  {len(profile_list)} profiles loaded."})
                if skipped_excluded:
                    self._emit("log", {"lvl": "info", "msg": f"  {skipped_excluded} profile(s) excluded by user — skipped."})
                if skipped_used:
                    self._emit("log", {"lvl": "info", "msg": f"  {skipped_used} profile(s) already registered on site #{site_id} — skipped."})
            else:
                self._emit("log", {"lvl": "warn", "msg": f"  Could not load profiles: {result.get('error')}"})

        if auto_mode and not profile_list:
            self._emit("log", {"lvl": "error", "msg": "Auto mode requires profiles — load your GoLogin API token first."})
            self._running = False
            self._emit("finished", {"ok": 0, "total": total, "results": []})
            return

        if auto_mode and len(profile_list) < total:
            self._emit("log", {"lvl": "warn", "msg": f"  ⚠ Only {len(profile_list)} profiles for {total} rows — extra rows will be skipped."})

        ACCESS_FAIL_PHRASES = (
            "site not accessible", "geo-blocked", "site blocked",
            "site unreachable", "profile may not have access",
            "profile may lack access",
        )

        def _is_access_failure(message: str) -> bool:
            low = message.lower()
            return any(p in low for p in ACCESS_FAIL_PHRASES)

        async with async_playwright() as pw:
            profile_idx = 0  # tracks which profile to use next in auto mode

            for i, row in enumerate(rows):
                if self._stop:
                    self._emit("log", {"lvl": "warn", "msg": "Stopped by user."})
                    break

                label = row.get("email") or row.get("username") or row.get("Email") or f"Row {i+1}"

                self._emit("progress", {"i": i, "total": total, "label": label})
                self._emit("log", {"lvl": "info", "msg": f"[{i+1}/{total}] {label}"})

                # ── Resolve profile ID ──
                if auto_mode:
                    if profile_idx >= len(profile_list):
                        msg = "No more profiles available"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue
                    pid = profile_list[profile_idx]["id"]
                    pname = profile_list[profile_idx]["name"]
                    self._emit("log", {"lvl": "info", "msg": f"  Auto-assigned profile: {pname} ({pid[:8]}…)"})
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
                        self._emit("log", {"lvl": "info", "msg": f"  Resolved '{raw_pid}' -> {pid[:8]}..."})
                    else:
                        msg = (
                            f"Profile '{raw_pid}' not found. "
                            "Check your GoLogin API token and profile names."
                        )
                        self._results.append({**row, "bot_status": "FAIL", "bot_message": msg})
                        self._emit("log",      {"lvl": "error", "msg": f"  ✗ {msg}"})
                        self._emit("row_done", {"i": i, "status": "FAIL", "label": label})
                        continue

                    if pid in excluded_ids:
                        msg = f"Profile '{raw_pid}' is excluded by user — skipped"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue

                    if pid in already_used_ids:
                        msg = f"Profile '{raw_pid}' already registered on site #{site_id} — skipped"
                        self._results.append({**row, "bot_status": "SKIP", "bot_message": msg})
                        self._emit("log",      {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        self._emit("row_done", {"i": i, "status": "SKIP", "label": label})
                        continue

                # ── Try profile, retry with next on access failure ──
                max_retries = len(profile_list) - profile_idx if auto_mode else 1
                ok = False
                msg = ""

                for attempt in range(max_retries):
                    if self._stop:
                        break

                    self._emit("log", {"lvl": "info", "msg": "  Starting GoLogin profile…"})
                    ws = await self._start_profile(token, pid)
                    if not ws:
                        msg = "GoLogin profile failed to start"
                        self._emit("log", {"lvl": "error", "msg": f"  ✗ {msg}"})
                        await self._stop_profile()
                        if auto_mode:
                            profile_idx += 1
                            if profile_idx < len(profile_list):
                                pid = profile_list[profile_idx]["id"]
                                pname = profile_list[profile_idx]["name"]
                                self._emit("log", {"lvl": "warn", "msg": f"  Trying next profile: {pname} ({pid[:8]}…)"})
                                continue
                        break

                    self._emit("log", {"lvl": "info", "msg": "  Profile started, connecting…"})
                    await asyncio.sleep(settings.get("profile_boot_wait", 5))

                    ok, msg = await self._fill(pw, ws, row, settings, field_map)
                    await self._stop_profile()

                    if not ok and _is_access_failure(msg) and auto_mode:
                        self._emit("log", {"lvl": "warn", "msg": f"  ⚠ {msg}"})
                        profile_idx += 1
                        if profile_idx < len(profile_list):
                            pid = profile_list[profile_idx]["id"]
                            pname = profile_list[profile_idx]["name"]
                            self._emit("log", {"lvl": "info", "msg": f"  Switching to next profile: {pname} ({pid[:8]}…)"})
                            wait = max(settings.get("delay_between_runs", 2), 3)
                            await asyncio.sleep(wait)
                            continue
                        else:
                            msg = "No more profiles with site access available"
                    break

                status = "OK" if ok else "FAIL"
                icon   = "✓" if ok else "✗"
                lvl    = "ok" if ok else "error"
                self._results.append({**row, "bot_status": status, "bot_message": msg})
                self._emit("log",      {"lvl": lvl,  "msg": f"  {icon} {msg}"})
                self._emit("row_done", {"i": i, "status": status, "label": label})
                if ok:
                    ok_count += 1
                    self._mark_profile_used(pid, site_id)
                    already_used_ids.add(pid)

                if auto_mode:
                    profile_idx += 1

                if i < total - 1 and not self._stop:
                    wait = max(settings.get("delay_between_runs", 2), 5)
                    self._emit("log", {"lvl": "info", "msg": f"  Waiting {wait}s before next profile…"})
                    await asyncio.sleep(wait)

        self._running = False
        site_id = settings.get("selected_site", "1")
        self._save_run_record(site_id, ok_count, total, self._results)
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
            print("[INFO] Stopping GoLogin profile...", flush=True)
            loop = asyncio.get_event_loop()
            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, gl.stop),
                    timeout=15
                )
                print("[INFO] GoLogin profile stopped.", flush=True)
            except asyncio.TimeoutError:
                print("[WARN] Profile stop timed out - forcing cleanup.", flush=True)
            except Exception as e:
                print(f"[WARN] Error stopping profile: {e}", flush=True)
            self._current_gl = None
            await asyncio.sleep(2)

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
        if col == "__province_of_residence_code__":
            return str(row.get("Province of residence", "")).strip().lower()
        if col == "__birthday__":
            raw = str(row.get("Birthday", "") or row.get("birthday", "")).strip()
            return format_birthday(raw)
        if col == "__birth_day__":
            raw = str(row.get("Birthday", "") or row.get("birthday", "")).strip()
            parts = raw.split("/")
            return parts[0] if len(parts) >= 3 else ""
        if col == "__birth_month__":
            raw = str(row.get("Birthday", "") or row.get("birthday", "")).strip()
            parts = raw.split("/")
            return parts[1] if len(parts) >= 3 else ""
        if col == "__birth_year__":
            raw = str(row.get("Birthday", "") or row.get("birthday", "")).strip()
            parts = raw.split("/")
            return parts[2] if len(parts) >= 3 else ""
        if col == "__gender__":
            code = str(row.get("Gender", "") or row.get("gender", "")).strip().upper()
            return GENDER_MAP.get(code, code)
        if col == "__house_number__":
            raw = str(row.get("House number", "")).strip()
            return raw.split(" ")[0] if raw else ""
        if col == "__security_question__":
            return "Qual è il tuo secondo nome?"
        if col == "__security_question_site5__":
            return "La mia squadra del cuore"
        if col == "__deposit_limit_site5__":
            return "99000 €"
        if col == "__security_question_site4__":
            return "Come si chiama tua madre"
        if col == "__security_answer_site4__":
            return "Piera"
        if col == "__profession_site4__":
            return "ALTRO"
        if col == "__bonus_text__":
            return self._current_settings.get("bonus_selection", "Casino")
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
        if col == "__issue_day__":
            raw = str(row.get("Issue date", "")).strip()
            parts = raw.split("/")
            return parts[0] if len(parts) >= 3 else ""
        if col == "__issue_month__":
            raw = str(row.get("Issue date", "")).strip()
            parts = raw.split("/")
            return parts[1] if len(parts) >= 3 else ""
        if col == "__issue_year__":
            raw = str(row.get("Issue date", "")).strip()
            parts = raw.split("/")
            return parts[2] if len(parts) >= 3 else ""
        if col == "__expiry_day__":
            raw = str(row.get("Expiration date", "")).strip()
            parts = raw.split("/")
            return parts[0] if len(parts) >= 3 else ""
        if col == "__expiry_month__":
            raw = str(row.get("Expiration date", "")).strip()
            parts = raw.split("/")
            return parts[1] if len(parts) >= 3 else ""
        if col == "__expiry_year__":
            raw = str(row.get("Expiration date", "")).strip()
            parts = raw.split("/")
            return parts[2] if len(parts) >= 3 else ""
        if col == "__phone_local__":
            phone = str(row.get("Telephone", "") or row.get("telephone", "")).strip()
            if phone.startswith("+39"):
                phone = phone[3:]
            elif phone.startswith("39") and len(phone) > 10:
                phone = phone[2:]
            return phone
        if col == "__phone_with_prefix__":
            phone = str(row.get("Telephone", "") or row.get("telephone", "")).strip()
            if phone.startswith("+39"):
                return phone
            if phone.startswith("39") and len(phone) > 10:
                return "+" + phone
            return "+39" + phone
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
                mouse = getattr(page, 'mouse', None) or page.page.mouse
                await mouse.move(tx, ty, steps=random.randint(8, 15))
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass

    @staticmethod
    def _kb(page_or_frame):
        """Get keyboard from Page or Frame (Frame has no .keyboard, use .page)."""
        return getattr(page_or_frame, 'keyboard', None) or page_or_frame.page.keyboard

    async def _human_type(self, page, selector, value):
        """Type text character by character with random human-like delays."""
        kb = self._kb(page)
        el = page.locator(selector).first
        await el.click()
        await el.press("Control+a")
        await kb.press("Backspace")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        for ch in value:
            await kb.type(ch)
            await asyncio.sleep(random.uniform(0.05, 0.18))
        await el.dispatch_event("input")
        await el.dispatch_event("change")
        await kb.press("Tab")
        await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _random_pause(self, short=False):
        """Random pause to break robotic timing patterns."""
        if short:
            await asyncio.sleep(random.uniform(0.3, 0.8))
        else:
            await asyncio.sleep(random.uniform(0.8, 2.0))

    async def _diagnose_submit_button(self, page, selector):
        """
        Inspect a submit button that is reported disabled and emit the root cause.
        Read-only: never clicks, never bypasses validation.
        Reports: locator match count & per-match state, aria/disabled, visibility/occlusion,
        enclosing form validity, invalid/pending/required form controls.

        The selector arg is a Playwright selector (may use :has-text() and other
        engines beyond CSS), so we resolve matches through Playwright's locator API
        and then hand the real DOM elements to an in-page evaluator.
        """
        describe_js = """(nodes) => {
                    const out = {matches: [], form: null, invalid: [], pending: [], required_empty: [], occluder: null};
                    out.match_count = nodes.length;
                    const describe = (el) => {
                        const r = el.getBoundingClientRect();
                        const cs = getComputedStyle(el);
                        const native = el.matches('button,input') ? el : el.querySelector('button,input');
                        return {
                            tag: el.tagName,
                            text: (el.innerText || '').trim().slice(0, 60),
                            classes: el.className,
                            disabled_prop: !!(native && native.disabled),
                            aria_disabled: el.getAttribute('aria-disabled'),
                            has_mat_disabled_class: /\\bmat-(mdc-)?button-disabled\\b/.test(el.className)
                                || (native ? /\\bmat-(mdc-)?button-disabled\\b/.test(native.className) : false),
                            visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none',
                            in_viewport: r.top >= 0 && r.left >= 0
                                && r.bottom <= (window.innerHeight || document.documentElement.clientHeight)
                                && r.right <= (window.innerWidth || document.documentElement.clientWidth),
                            rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                        };
                    };
                    nodes.slice(0, 5).forEach(el => out.matches.push(describe(el)));

                    const btn = nodes[0];
                    if (btn) {
                        const r = btn.getBoundingClientRect();
                        const cx = Math.round(r.x + r.width / 2);
                        const cy = Math.round(r.y + r.height / 2);
                        const top = document.elementFromPoint(cx, cy);
                        if (top && top !== btn && !btn.contains(top) && !top.contains(btn)) {
                            out.occluder = {
                                tag: top.tagName,
                                id: top.id,
                                classes: top.className,
                                text: (top.innerText || '').trim().slice(0, 60),
                            };
                        }
                        const form = btn.closest('form');
                        if (form) {
                            out.form = {
                                classes: form.className,
                                ng_invalid: form.classList.contains('ng-invalid'),
                                ng_pending: form.classList.contains('ng-pending'),
                                ng_dirty: form.classList.contains('ng-dirty'),
                                ng_touched: form.classList.contains('ng-touched'),
                            };
                        }
                    }

                    // Angular Material / reactive-form field diagnostics via CSS classes
                    const fields = Array.from(document.querySelectorAll('[formcontrolname]'));
                    for (const f of fields) {
                        const name = f.getAttribute('formcontrolname') || '';
                        const cls = f.className || '';
                        const invalid = cls.includes('ng-invalid');
                        const pending = cls.includes('ng-pending');
                        if (invalid) {
                            let val = '';
                            const inp = f.matches('input,select,textarea') ? f : f.querySelector('input,select,textarea');
                            if (inp) val = (inp.value || '').slice(0, 40);
                            const req = (inp && (inp.required || inp.getAttribute('aria-required') === 'true'))
                                        || f.getAttribute('aria-required') === 'true';
                            out.invalid.push({name, tag: f.tagName, has_value: !!val, value_preview: val, required: !!req, classes: cls.slice(0, 120)});
                            if (req && !val) out.required_empty.push(name);
                        }
                        if (pending) out.pending.push(name);
                    }

                    // Mat-form-field level invalid flag (covers checkboxes/radios where class lives on wrapper)
                    const matInvalid = Array.from(document.querySelectorAll('.mat-form-field-invalid, .mat-mdc-form-field-invalid'));
                    out.mat_form_field_invalid_count = matInvalid.length;

                    return out;
                }"""
        try:
            handles = await page.locator(selector).element_handles()
            # Each ElementHandle in the list is serialized to its real DOM node
            # when the list is passed as a single arg to evaluate().
            report = await page.evaluate(describe_js, handles[:5])
        except Exception as diag_err:
            self._emit("log", {"lvl": "warn", "msg": f"    diagnose: evaluate failed: {diag_err}"})
            return

        mc = report.get("match_count", 0)
        self._emit("log", {"lvl": "warn", "msg": f"    diagnose: selector matched {mc} element(s)"})
        for i, m in enumerate(report.get("matches", [])):
            self._emit("log", {"lvl": "warn", "msg": (
                f"      [{i}] <{m.get('tag')}> text='{m.get('text')}' "
                f"disabled={m.get('disabled_prop')} aria-disabled={m.get('aria_disabled')} "
                f"mat-disabled-class={m.get('has_mat_disabled_class')} "
                f"visible={m.get('visible')} in_viewport={m.get('in_viewport')} rect={m.get('rect')}"
            )})
        occ = report.get("occluder")
        if occ:
            self._emit("log", {"lvl": "warn", "msg": (
                f"    diagnose: button covered by <{occ.get('tag')}> "
                f"id='{occ.get('id')}' classes='{str(occ.get('classes'))[:80]}' "
                f"text='{occ.get('text')}'"
            )})
        form = report.get("form")
        if form:
            self._emit("log", {"lvl": "warn", "msg": (
                f"    diagnose: enclosing form ng-invalid={form.get('ng_invalid')} "
                f"ng-pending={form.get('ng_pending')} ng-touched={form.get('ng_touched')}"
            )})
        pending = report.get("pending") or []
        if pending:
            self._emit("log", {"lvl": "warn", "msg": f"    diagnose: async-pending controls: {pending}"})
        req_empty = report.get("required_empty") or []
        if req_empty:
            self._emit("log", {"lvl": "warn", "msg": f"    diagnose: REQUIRED controls with empty value: {req_empty}"})
        invalid = report.get("invalid") or []
        for ctl in invalid[:12]:
            self._emit("log", {"lvl": "warn", "msg": (
                f"      invalid: {ctl.get('name')} tag={ctl.get('tag')} "
                f"required={ctl.get('required')} has_value={ctl.get('has_value')} "
                f"value='{ctl.get('value_preview')}'"
            )})
        if report.get("mat_form_field_invalid_count"):
            self._emit("log", {"lvl": "warn", "msg": (
                f"    diagnose: {report['mat_form_field_invalid_count']} mat-form-field marked invalid"
            )})
        if not form and not invalid and not pending and mc == 0:
            self._emit("log", {"lvl": "warn", "msg": "    diagnose: no match + no form state — selector likely wrong page/wrong button"})

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
            # Skip disabled/readonly fields for fill/select types (pre-populated by server)
            if field_type in ("fill", "append", "select", "select_label", "select_postback", "date", "autocomplete"):
                try:
                    state = await page.locator(selector).first.evaluate(
                        "el => ({disabled: el.disabled, readonly: el.readOnly || el.hasAttribute('readonly')})"
                    )
                    if state.get("disabled") or state.get("readonly"):
                        self._emit("log", {"lvl": "info", "msg": f"    Field {selector[:50]} is disabled/readonly, skipping"})
                        return
                except Exception:
                    pass
            await self._move_to_element(page, selector)
        await self._random_pause(short=True)
        if field_type == "fill":
            await self._human_type(page, selector, value)
        elif field_type == "append":
            kb = self._kb(page)
            el = page.locator(selector).first
            await el.click()
            await kb.press("End")
            await asyncio.sleep(random.uniform(0.1, 0.3))
            v = value.strip()
            if v.startswith("+39"):
                v = v[3:]
            elif v.startswith("39") and len(v) > 10:
                v = v[2:]
            value = v
            for ch in value:
                await kb.type(ch)
                await asyncio.sleep(random.uniform(0.05, 0.18))
            await el.dispatch_event("input")
            await el.dispatch_event("change")
            await kb.press("Tab")
            await asyncio.sleep(random.uniform(0.1, 0.3))
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
        elif field_type == "gogoal_dropdown":
            trigger = (field_cfg or {}).get("trigger", "")
            smap = (field_cfg or {}).get("selector_map", {})
            option_label = smap.get(value, value)
            if trigger:
                await page.click(trigger)
                await self._random_pause()
                panel = page.locator(".form-dropdown__options, .form-dropdown__panel, [class*='dropdown']:visible")
                option = panel.get_by_text(option_label, exact=False).first
                try:
                    await option.wait_for(state="visible", timeout=5000)
                    await option.click()
                except Exception:
                    try:
                        option2 = page.get_by_text(option_label, exact=False).first
                        await option2.wait_for(state="visible", timeout=3000)
                        await option2.click()
                    except Exception:
                        self._emit("log", {"lvl": "warn", "msg": f"    Dropdown option '{option_label}' not found, skipping"})
                await self._random_pause(short=True)
        elif field_type == "select":
            await page.select_option(selector, value)
        elif field_type == "select_label":
            await page.select_option(selector, label=value)
        elif field_type == "select_postback":
            await page.select_option(selector, value)
            await asyncio.sleep(0.3)
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                await asyncio.sleep(2)
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
            try:
                el_info = await el.evaluate("""el => {
                    const info = {tag: el.tagName, id: el.id, type: el.type,
                        onclick: el.getAttribute('onclick'), value: el.value, href: el.href,
                        html: el.outerHTML.substring(0, 200)};
                    // Extract referenced JS function source
                    const oc = el.getAttribute('onclick') || '';
                    const fnMatch = oc.match(/^(\\w+)\\(/);
                    if (fnMatch && typeof window[fnMatch[1]] === 'function')
                        info.fn_source = window[fnMatch[1]].toString().substring(0, 500);
                    return info;
                }""")
                print(f"[DEBUG] click_first target: {el_info}", flush=True)
            except Exception:
                pass
            try:
                await el.click(timeout=5000)
            except Exception as e:
                # Overlay intercepting pointer events (styled checkboxes, custom controls) — force click
                msg = str(e).lower()
                if "intercepts pointer events" in msg or "intercept" in msg:
                    try:
                        await el.click(force=True, timeout=3000)
                        print(f"[DEBUG] click_first force-click succeeded", flush=True)
                    except Exception as e2:
                        try:
                            await el.evaluate("el => el.click()")
                            print(f"[DEBUG] click_first JS click succeeded", flush=True)
                        except Exception as e3:
                            print(f"[DEBUG] click_first all methods failed: {e3}", flush=True)
                else:
                    print(f"[DEBUG] click_first error: {e}", flush=True)
        elif field_type == "js_eval":
            # Execute arbitrary JS expression (e.g. "signUP('')")
            print(f"[DEBUG] js_eval: {selector}", flush=True)
            try:
                await page.evaluate(selector)
            except Exception as e:
                print(f"[DEBUG] js_eval error: {e}", flush=True)
        elif field_type == "click_nav":
            el = page.locator(selector).first
            await el.scroll_into_view_if_needed()
            await self._random_pause(short=True)
            try:
                await el.click()
            except Exception as e:
                print(f"[DEBUG] click_nav click error (expected if page navigated): {e}", flush=True)
            await asyncio.sleep(2)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                print("[DEBUG] click_nav wait_for_load_state failed (page may have changed)", flush=True)
        elif field_type == "click_popup":
            # Intercept window.open before clicking, capture the URL, then navigate
            try:
                # Monkey-patch window.open to capture URL instead of opening popup
                await page.evaluate("""() => {
                    window.__popupUrl = null;
                    window.__origOpen = window.open;
                    window.open = function(url, name, features) {
                        window.__popupUrl = url;
                        return { document: { write: function(){}, close: function(){} }, close: function(){}, focus: function(){} };
                    };
                }""")
                el = page.locator(selector).first
                await el.scroll_into_view_if_needed()
                await self._random_pause(short=True)
                await el.click()
                await asyncio.sleep(2)
                popup_url = await page.evaluate("window.__popupUrl")
                print(f"[DEBUG] Intercepted popup URL: {popup_url}", flush=True)
                # Restore original window.open
                await page.evaluate("if(window.__origOpen) window.open = window.__origOpen;")
                if popup_url:
                    if not popup_url.startswith("http"):
                        base = page.url.split("//")[0] + "//" + page.url.split("//")[1].split("/")[0]
                        popup_url = base + ("/" if not popup_url.startswith("/") else "") + popup_url
                    print(f"[DEBUG] Navigating to: {popup_url}", flush=True)
                    await page.goto(popup_url, wait_until="domcontentloaded", timeout=15000)
                else:
                    print("[DEBUG] No popup URL intercepted, trying direct signUP call", flush=True)
                    # Try extracting from signUP function source
                    reg_url = await page.evaluate("""() => {
                        if (typeof signUP === 'function') {
                            const src = signUP.toString();
                            const m = src.match(/['"]([^'"]*(?:regist|signup)[^'"]*)['"]/i);
                            if (m) return m[1];
                        }
                        return null;
                    }""")
                    if reg_url:
                        if not reg_url.startswith("http"):
                            base = page.url.split("//")[0] + "//" + page.url.split("//")[1].split("/")[0]
                            reg_url = base + ("/" if not reg_url.startswith("/") else "") + reg_url
                        print(f"[DEBUG] Navigating to extracted URL: {reg_url}", flush=True)
                        await page.goto(reg_url, wait_until="domcontentloaded", timeout=15000)
            except Exception as e:
                print(f"[DEBUG] click_popup error: {e}", flush=True)
        elif field_type == "autocomplete":
            kb = self._kb(page)
            await page.click(selector)
            await page.fill(selector, "")
            await self._random_pause(short=True)
            for ch in value:
                await kb.type(ch)
                await asyncio.sleep(random.uniform(0.05, 0.18))
            el = page.locator(selector).first
            await el.dispatch_event("input")
            await asyncio.sleep(1.5)
            dropdown = page.locator("mat-option, [role='listbox'] [role='option'], .autocomplete-suggestion, .MuiAutocomplete-option, ng-dropdown-panel .ng-option, .ng-dropdown-panel-items .ng-option").first
            try:
                await dropdown.wait_for(state="visible", timeout=5000)
                await self._random_pause(short=True)
                await dropdown.click()
            except Exception:
                await kb.press("ArrowDown")
                await kb.press("Enter")
            await self._random_pause(short=True)
        elif field_type == "file_upload":
            id_folder = getattr(self, "_cur_settings", {}).get("id_folder", "")
            if id_folder:
                file_path = Path(id_folder) / value
            else:
                file_path = USER_DATA_DIR / "IDs" / value
            if not file_path.exists():
                self._emit("log", {"lvl": "warn", "msg": f"    File not found: {file_path}"})
                return
            # Diagnose which element matched
            try:
                count = await page.locator(selector).count()
                if count == 0:
                    self._emit("log", {"lvl": "error", "msg": f"    file_upload: no element matched {selector}"})
                    return
                el_info = await page.locator(selector).first.evaluate(
                    "el => ({tag: el.tagName, id: el.id, type: el.type, name: el.name})"
                )
                print(f"[DEBUG] file_upload target (matches={count}): {el_info}", flush=True)
            except Exception as diag_err:
                print(f"[DEBUG] file_upload diag error: {diag_err}", flush=True)
            await page.set_input_files(selector, str(file_path))
            try:
                el = page.locator(selector).first
                await el.dispatch_event("change")
                await el.dispatch_event("input")
            except Exception:
                pass
            await asyncio.sleep(3)
        elif field_type == "doc_upload":
            id_folder = getattr(self, "_cur_settings", {}).get("id_folder", "")
            front_file = value.strip()
            if not front_file:
                self._emit("log", {"lvl": "warn", "msg": "    No front image specified, skipping doc upload"})
                return
            if id_folder:
                front_path = Path(id_folder) / front_file
            else:
                front_path = USER_DATA_DIR / "IDs" / front_file
            if not front_path.exists():
                self._emit("log", {"lvl": "warn", "msg": f"    Front image not found: {front_path}"})
                return
            self._emit("log", {"lvl": "info", "msg": f"    Uploading document: {front_path.name}"})
            try:
                async with page.expect_file_chooser(timeout=10000) as fc_info:
                    await page.click(selector, timeout=5000)
                file_chooser = await fc_info.value
                await file_chooser.set_files(str(front_path))
                self._emit("log", {"lvl": "info", "msg": f"    Document uploaded successfully"})
                await asyncio.sleep(5)
                # Check if registration failure page appeared after upload
                fail_el = page.locator("text=La registrazione non è andata a buon fine")
                try:
                    await fail_el.wait_for(state="visible", timeout=5000)
                    raise Exception("DOC_UPLOAD_FAIL: Registration failed after document upload")
                except PWTimeout:
                    pass
            except Exception as e:
                if "DOC_UPLOAD_FAIL" in str(e):
                    raise
                self._emit("log", {"lvl": "warn", "msg": f"    Doc upload error: {e}"})
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
            _disconnected = {"flag": False}
            page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
            page.on("crash", lambda: print("[WARN] Page crashed!", flush=True))
            def _on_disconnect():
                _disconnected["flag"] = True
                print("[WARN] Browser disconnected!", flush=True)
            browser.on("disconnected", _on_disconnect)
            url = settings["registration_url"]
            self._emit("log", {"lvl": "info", "msg": f"    Navigating to {url}"})
            resp = None
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except PWTimeout:
                return False, "Site unreachable — page load timed out (profile may lack access)"
            except Exception as nav_err:
                print(f"[DEBUG] goto threw: {nav_err}, disconnected={_disconnected['flag']}", flush=True)
                if not _disconnected["flag"]:
                    await asyncio.sleep(3)
                if _disconnected["flag"]:
                    self._emit("log", {"lvl": "info", "msg": f"    CDP disconnected during navigation, reconnecting..."})
                    await asyncio.sleep(3)
                    import re as _re
                    port_match = _re.search(r':(\d{4,5})/', ws)
                    port_num = int(port_match.group(1)) if port_match else None
                    new_ws = None
                    if port_num:
                        for _retry in range(5):
                            try:
                                async with aiohttp.ClientSession() as _s:
                                    async with _s.get(f"http://127.0.0.1:{port_num}/json/version", timeout=aiohttp.ClientTimeout(total=3)) as _r:
                                        if _r.status == 200:
                                            _data = await _r.json(content_type=None)
                                            new_ws = _data.get("webSocketDebuggerUrl", "")
                                            if new_ws:
                                                break
                            except Exception:
                                pass
                            await asyncio.sleep(1)
                    print(f"[DEBUG] Fresh WS after goto: {new_ws}", flush=True)
                    if not new_ws:
                        return False, "Browser process unreachable after navigation disconnect"
                    try:
                        browser = await pw.chromium.connect_over_cdp(new_ws)
                        ws = new_ws
                        _disconnected["flag"] = False
                        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
                        page = ctx.pages[-1] if ctx.pages else await ctx.new_page()
                        page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
                        def _on_disconnect_nav():
                            _disconnected["flag"] = True
                            print("[WARN] Browser disconnected!", flush=True)
                        browser.on("disconnected", _on_disconnect_nav)
                        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                        self._emit("log", {"lvl": "info", "msg": f"    Reconnected after goto! Page: {page.url[:80]}"})
                    except Exception as reconn_err:
                        return False, f"Reconnect after navigation failed: {reconn_err}"
                else:
                    return False, f"Site unreachable — {nav_err}"

            # Check if navigation opened a new tab
            if not _disconnected["flag"]:
                await asyncio.sleep(1)
                try:
                    if len(ctx.pages) > 1 and ctx.pages[-1] != page:
                        page = ctx.pages[-1]
                        self._emit("log", {"lvl": "info", "msg": f"    Switched to new tab after navigation"})
                        await page.wait_for_load_state("domcontentloaded", timeout=15_000)

                    if page.is_closed():
                        if len(ctx.pages) > 0:
                            page = ctx.pages[-1]
                            self._emit("log", {"lvl": "info", "msg": f"    Original page closed, switched to active page"})
                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                        else:
                            return False, "Page closed unexpectedly"
                except Exception:
                    pass

            if resp and resp.status in (403, 451, 503):
                return False, f"Site blocked (HTTP {resp.status}) - this profile may not have access"

            try:
                blocked = await page.evaluate("""() => {
                    const t = document.title.toLowerCase();
                    const b = document.body ? document.body.innerText.substring(0, 500).toLowerCase() : '';
                    if (t.includes('access denied') || t.includes('blocked') || t.includes('forbidden')
                        || t.includes('not available') || t.includes('geo') || t.includes('restricted'))
                        return true;
                    if (b.includes('access denied') || b.includes('not available in your')
                        || b.includes('geo-restrict') || b.includes('blocked')
                        || b.includes('this site is not accessible') || b.includes('your region'))
                        return true;
                    return false;
                }""")
                if blocked:
                    return False, "Site not accessible from this profile — geo-blocked or restricted"
            except Exception:
                if _disconnected["flag"]:
                    pass  # already disconnected, will be handled later
                else:
                    return False, "Cannot evaluate page — possible disconnect"

            await self._inject_cursor(page)
            await self._random_pause()

            steps = settings.get("steps") or []

            # Listen for popups (new windows opened by JS)
            popup_pages = []
            ctx.on("page", lambda p: popup_pages.append(p))

            if steps:
                for si, step in enumerate(steps):
                    step_fields = step.get("fields", [])
                    step_submit = step.get("submit_selector", "")
                    wait_sel    = step.get("wait_after", "")
                    optional    = step.get("optional", False)
                    fail_sel    = step.get("fail_selector", "")

                    self._emit("log", {"lvl": "info", "msg": f"  Step {si+1}: {step.get('name', f'Page {si+1}')}"})
                    await self._random_pause()

                    # Resolve iframe if step requires it
                    iframe_sel = step.get("iframe", "")
                    target = page  # default: operate on main page
                    if iframe_sel:
                        try:
                            iframe_el = page.locator(iframe_sel)
                            await iframe_el.wait_for(state="visible", timeout=20_000)
                            # Get iframe src to find the Frame object by URL
                            iframe_src = await iframe_el.get_attribute("src") or ""
                            print(f"[DEBUG] Iframe src: {iframe_src}", flush=True)
                            frame = None
                            # Try by URL match first
                            if iframe_src:
                                for f in page.frames:
                                    if iframe_src in (f.url or ""):
                                        frame = f
                                        break
                            # Fallback: try by name/id
                            if not frame:
                                iframe_name = await iframe_el.get_attribute("name") or await iframe_el.get_attribute("id") or ""
                                if iframe_name:
                                    frame = page.frame(name=iframe_name)
                            # Fallback: second frame (first is main)
                            if not frame and len(page.frames) > 1:
                                frame = page.frames[1]
                            if frame:
                                target = frame
                                self._emit("log", {"lvl": "info", "msg": f"    Using iframe: {iframe_sel} -> {frame.url[:80]}"})
                                await frame.wait_for_load_state("domcontentloaded", timeout=15_000)
                            else:
                                self._emit("log", {"lvl": "warn", "msg": f"    Iframe {iframe_sel} found but no Frame object (frames: {len(page.frames)})"})
                        except Exception as iframe_err:
                            if optional:
                                self._emit("log", {"lvl": "info", "msg": f"    Optional step skipped (iframe not found)"})
                                continue
                            self._emit("log", {"lvl": "error", "msg": f"    Iframe {iframe_sel} not available: {iframe_err}"})
                            raise

                    await self._inject_cursor(page)

                    try:
                        for m in step_fields:
                            col  = m.get("csv_col", "")
                            sel  = m.get("selector", "")
                            ftype = m.get("type", "fill")

                            if sel == "__dynamic_bonus__":
                                bonus = self._current_settings.get("bonus_selection", "Casino")
                                sel = f"mat-radio-group[formcontrolname='bonus'] app-bonus-item:has-text('{bonus}') mat-radio-button"

                            if not sel and ftype not in ("gogoal_dropdown",):
                                continue

                            if optional:
                                try:
                                    await target.wait_for_selector(sel, timeout=8000)
                                except PWTimeout:
                                    self._emit("log", {"lvl": "info", "msg": f"    Optional step skipped"})
                                    raise _SkipStep()

                            if ftype == "click_popup":
                                self._emit("log", {"lvl": "info", "msg": f"    {ftype}: {sel[:60]}"})
                                popup_page = await self._apply_field(page, sel, "", ftype)
                                if popup_page:
                                    page = popup_page
                                    target = page
                                    self._emit("log", {"lvl": "info", "msg": f"    Switched to popup window"})
                                    await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                            elif ftype in ("radio", "click", "click_first", "click_nav", "js_eval"):
                                self._emit("log", {"lvl": "info", "msg": f"    {ftype}: {sel[:60]}"})
                                try:
                                    await self._apply_field(target, sel, "", ftype)
                                except Exception as click_ex:
                                    print(f"[DEBUG] {ftype} threw: {click_ex}", flush=True)
                                # After click on main page, wait for potential disconnect
                                if not iframe_sel:
                                    for _dw in range(8):
                                        await asyncio.sleep(1)
                                        if _disconnected["flag"]:
                                            break
                                    print(f"[DEBUG] After {ftype}: flag={_disconnected['flag']}, waited={_dw+1}s", flush=True)
                                else:
                                    await asyncio.sleep(0.5)
                                connected = not _disconnected["flag"]
                                if not connected:
                                    self._emit("log", {"lvl": "info", "msg": f"    Browser disconnected after {ftype}, reconnecting..."})
                                    await asyncio.sleep(3)
                                    # Fetch fresh websocket URL from browser debug endpoint
                                    import re as _re
                                    port_match = _re.search(r':(\d{4,5})/', ws)
                                    port_num = int(port_match.group(1)) if port_match else None
                                    new_ws = None
                                    if port_num:
                                        for _retry in range(5):
                                            try:
                                                async with aiohttp.ClientSession() as _s:
                                                    async with _s.get(f"http://127.0.0.1:{port_num}/json/version", timeout=aiohttp.ClientTimeout(total=3)) as _r:
                                                        if _r.status == 200:
                                                            _data = await _r.json(content_type=None)
                                                            new_ws = _data.get("webSocketDebuggerUrl", "")
                                                            if new_ws:
                                                                break
                                            except Exception:
                                                pass
                                            await asyncio.sleep(1)
                                    print(f"[DEBUG] Fresh WS URL: {new_ws}", flush=True)
                                    if not new_ws:
                                        self._emit("log", {"lvl": "error", "msg": f"    Cannot get fresh WS URL from port {port_num}"})
                                        raise Exception("Browser process unreachable for reconnect")
                                    try:
                                        browser = await pw.chromium.connect_over_cdp(new_ws)
                                        ws = new_ws
                                        _disconnected["flag"] = False
                                        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
                                        page = ctx.pages[-1] if ctx.pages else await ctx.new_page()
                                        page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
                                        def _on_disconnect2():
                                            _disconnected["flag"] = True
                                            print("[WARN] Browser disconnected!", flush=True)
                                        browser.on("disconnected", _on_disconnect2)
                                        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                                        self._emit("log", {"lvl": "info", "msg": f"    Reconnected! Page: {page.url[:80]}"})
                                    except Exception as reconn_err:
                                        self._emit("log", {"lvl": "error", "msg": f"    Reconnect failed: {reconn_err}"})
                                        raise
                            elif ftype == "check":
                                val = self._resolve_value(col, row) if col else ""
                                self._emit("log", {"lvl": "info", "msg": f"    check: {sel[:60]}"})
                                await self._apply_field(target, sel, val, ftype)
                            elif ftype == "radio_map":
                                val = self._resolve_value(col, row) if col else ""
                                if val:
                                    self._emit("log", {"lvl": "info", "msg": f"    radio_map: {val} -> {sel[:60]}"})
                                    await self._apply_field(target, sel, val, ftype, m)
                            elif ftype == "gogoal_dropdown":
                                val = self._resolve_value(col, row) if col else ""
                                if val:
                                    self._emit("log", {"lvl": "info", "msg": f"    gogoal_dropdown: {col} = {val}"})
                                    await self._apply_field(target, sel, val, ftype, m)
                            else:
                                fcfg = m.get("field_cfg", {})
                                if col:
                                    val = self._resolve_value(col, row)
                                elif fcfg.get("value"):
                                    val = fcfg["value"]
                                else:
                                    val = ""
                                if sel and val:
                                    self._emit("log", {"lvl": "info", "msg": f"    {ftype}: {col or '(fixed)'} -> {sel[:50]} = {val[:30]}"})
                                    await self._apply_field(target, sel, val, ftype)

                        # Check if browser disconnected and reconnect if needed
                        await asyncio.sleep(0.5)
                        if _disconnected["flag"]:
                            self._emit("log", {"lvl": "info", "msg": f"    Browser disconnected (post-fields), reconnecting..."})
                            await asyncio.sleep(2)
                            import re as _re
                            port_match = _re.search(r':(\d{4,5})/', ws)
                            port_num = int(port_match.group(1)) if port_match else None
                            new_ws = None
                            if port_num:
                                for _retry in range(5):
                                    try:
                                        async with aiohttp.ClientSession() as _s:
                                            async with _s.get(f"http://127.0.0.1:{port_num}/json/version", timeout=aiohttp.ClientTimeout(total=3)) as _r:
                                                if _r.status == 200:
                                                    _data = await _r.json(content_type=None)
                                                    new_ws = _data.get("webSocketDebuggerUrl", "")
                                                    if new_ws:
                                                        break
                                    except Exception:
                                        pass
                                    await asyncio.sleep(1)
                            try:
                                browser = await pw.chromium.connect_over_cdp(new_ws or ws)
                                ws = new_ws or ws
                                _disconnected["flag"] = False
                                ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
                                page = ctx.pages[-1] if ctx.pages else await ctx.new_page()
                                page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
                                def _on_disconnect_post():
                                    _disconnected["flag"] = True
                                    print("[WARN] Browser disconnected!", flush=True)
                                browser.on("disconnected", _on_disconnect_post)
                                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                                self._emit("log", {"lvl": "info", "msg": f"    Reconnected! Page: {page.url[:60]}"})
                            except Exception as reconn_err:
                                self._emit("log", {"lvl": "error", "msg": f"    Reconnect failed: {reconn_err}"})
                                return False, f"Browser disconnected and reconnect failed"
                        elif popup_pages:
                            page = popup_pages[-1]
                            popup_pages.clear()
                            self._emit("log", {"lvl": "info", "msg": f"    Switched to popup window"})
                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                        elif page.is_closed() and len(ctx.pages) > 0:
                            page = ctx.pages[-1]
                            self._emit("log", {"lvl": "info", "msg": f"    Page closed, switched to remaining page"})
                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                        elif len(ctx.pages) > 1 and ctx.pages[-1] != page:
                            page = ctx.pages[-1]
                            self._emit("log", {"lvl": "info", "msg": f"    Switched to new tab"})
                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)

                        if step_submit:
                            self._emit("log", {"lvl": "info", "msg": f"    Clicking submit: {step_submit[:60]}"})
                            await self._random_pause()
                            try:
                                btn = target.locator(step_submit).first
                                await btn.wait_for(state="visible", timeout=10_000)
                                try:
                                    await btn.scroll_into_view_if_needed(timeout=3000)
                                except Exception:
                                    pass
                                if not await btn.is_enabled():
                                    for _wait in range(30):
                                        await asyncio.sleep(1)
                                        if await btn.is_enabled():
                                            self._emit("log", {"lvl": "info", "msg": f"    Submit enabled after {_wait+1}s"})
                                            break
                                    else:
                                        self._emit("log", {"lvl": "warn", "msg": f"    Submit button still disabled after 30s"})
                                        await self._diagnose_submit_button(target, step_submit)
                                if not iframe_sel:
                                    await self._move_to_element(page, step_submit)
                                print(f"[DEBUG] Clicking submit button", flush=True)
                                await btn.click(timeout=15_000)
                                self._emit("log", {"lvl": "info", "msg": f"    Submit clicked"})
                            except Exception as submit_err:
                                print(f"[DEBUG] Submit error: {submit_err}, flag={_disconnected['flag']}", flush=True)
                                if not _disconnected["flag"]:
                                    raise
                            await asyncio.sleep(1)
                            if popup_pages:
                                page = popup_pages[-1]
                                target = page
                                popup_pages.clear()
                                self._emit("log", {"lvl": "info", "msg": f"    Switched to popup after submit"})
                                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                            elif not iframe_sel and page.is_closed() and len(ctx.pages) > 0:
                                page = ctx.pages[-1]
                                target = page
                                self._emit("log", {"lvl": "info", "msg": f"    Page closed after submit, switched"})
                                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                            elif wait_sel:
                                await target.wait_for_selector(wait_sel, timeout=15_000)
                            elif iframe_sel:
                                await asyncio.sleep(2)
                            else:
                                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                        elif wait_sel:
                            try:
                                await target.wait_for_selector(wait_sel, timeout=15_000)
                            except Exception as ws_err:
                                print(f"[DEBUG] wait_after threw: {ws_err}, flag={_disconnected['flag']}", flush=True)
                                if _disconnected["flag"]:
                                    # Reconnect and check wait_sel on the new page
                                    self._emit("log", {"lvl": "info", "msg": f"    CDP disconnected during wait_after, reconnecting..."})
                                    await asyncio.sleep(3)
                                    import re as _re
                                    port_match = _re.search(r':(\d{4,5})/', ws)
                                    port_num = int(port_match.group(1)) if port_match else None
                                    new_ws = None
                                    if port_num:
                                        for _retry in range(5):
                                            try:
                                                async with aiohttp.ClientSession() as _s:
                                                    async with _s.get(f"http://127.0.0.1:{port_num}/json/version", timeout=aiohttp.ClientTimeout(total=3)) as _r:
                                                        if _r.status == 200:
                                                            _data = await _r.json(content_type=None)
                                                            new_ws = _data.get("webSocketDebuggerUrl", "")
                                                            if new_ws:
                                                                break
                                            except Exception:
                                                pass
                                            await asyncio.sleep(1)
                                    print(f"[DEBUG] Fresh WS after wait_after: {new_ws}", flush=True)
                                    if new_ws:
                                        try:
                                            browser = await pw.chromium.connect_over_cdp(new_ws)
                                            ws = new_ws
                                            _disconnected["flag"] = False
                                            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
                                            page = ctx.pages[-1] if ctx.pages else await ctx.new_page()
                                            page.on("close", lambda: print("[WARN] Page was closed!", flush=True))
                                            def _on_disconnect_wa():
                                                _disconnected["flag"] = True
                                                print("[WARN] Browser disconnected!", flush=True)
                                            browser.on("disconnected", _on_disconnect_wa)
                                            await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                                            self._emit("log", {"lvl": "info", "msg": f"    Reconnected after wait_after! Page: {page.url[:80]}"})
                                            # Try wait_sel again on reconnected page
                                            try:
                                                await page.wait_for_selector(wait_sel, timeout=10_000)
                                            except Exception:
                                                self._emit("log", {"lvl": "warn", "msg": f"    wait_after selector not found after reconnect, continuing anyway"})
                                        except Exception as reconn_err:
                                            self._emit("log", {"lvl": "error", "msg": f"    Reconnect failed: {reconn_err}"})
                                            raise
                                    else:
                                        raise Exception("Browser unreachable for reconnect after wait_after")
                                else:
                                    raise

                        # Check for registration-failure page if step defines a fail_selector
                        if fail_sel:
                            try:
                                await page.locator(fail_sel).first.wait_for(state="visible", timeout=3000)
                                self._emit("log", {"lvl": "error", "msg": f"    Failure page detected: {fail_sel[:60]}"})
                                raise Exception(f"DOC_UPLOAD_FAIL: Failure page detected after step {step.get('name', '')}")
                            except PWTimeout:
                                pass
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
            msg = str(e)
            if "DOC_UPLOAD_FAIL" in msg:
                return False, "Registration failed after document upload"
            print(f"[ERROR] _fill exception: {e}", flush=True)
            traceback.print_exc()
            return False, msg
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass


# ── Launch ────────────────────────────────────────────────────────────────────
def _fatal(msg: str) -> None:
    """Show an error dialog, log to %LOCALAPPDATA%\\R-Bot\\UserData\\logs\\fatal.log, exit non-zero."""
    try:
        (USER_DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
        with open(USER_DATA_DIR / "logs" / "fatal.log", "a", encoding="utf-8") as fh:
            fh.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "R-Bot — Startup error", 0x10)
    except Exception:
        print(msg, file=sys.stderr)
    sys.exit(1)


try:
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
except Exception as _startup_err:
    _fatal(f"Failed to create the application window:\n\n{_startup_err}\n\n{traceback.format_exc()}")


if __name__ == "__main__":
    try:
        webview.start()
    except Exception as _run_err:
        _fatal(f"The application crashed:\n\n{_run_err}\n\n{traceback.format_exc()}")
