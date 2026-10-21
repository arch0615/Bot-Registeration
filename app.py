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

class _SkipStep(Exception):
    pass

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)


def generate_username(email: str) -> str:
    prefix = email.split("@")[0] if "@" in email else email
    username = re.sub(r'[^a-zA-Z0-9]', '', prefix)
    if len(username) < 6:
        username = username.ljust(6, '0')
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

    def _resolve_value(self, col, row):
        if col == "__username__":
            email = str(row.get("Email", "") or row.get("email", "")).strip()
            return generate_username(email)
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
        return str(row.get(col, "")).strip()

    CURSOR_INJECT_JS = """
    (() => {
        if (document.getElementById('__bot_cursor')) return;
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
        await page.click(selector)
        await page.fill(selector, "")
        for ch in value:
            await page.keyboard.type(ch)
            await asyncio.sleep(random.uniform(0.05, 0.18))

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
            await self._move_to_element(page, selector)
        await self._random_pause(short=True)
        if field_type == "fill":
            await self._human_type(page, selector, value)
        elif field_type == "check":
            if not value or value.lower() in ("true", "1", "yes", "si", "sì"):
                await page.check(selector)
            else:
                await page.uncheck(selector)
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
            browser = await pw.chromium.connect_over_cdp(ws)
            ctx  = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            await page.goto(
                settings["registration_url"],
                wait_until="domcontentloaded",
                timeout=30_000
            )
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
                                await self._apply_field(page, sel, "", ftype)
                            elif ftype == "check":
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

                        if step_submit:
                            await self._random_pause()
                            await self._move_to_element(page, step_submit)
                            await page.click(step_submit)
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
                await page.goto(
                    settings["registration_url"],
                    wait_until="domcontentloaded",
                    timeout=30_000
                )

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
