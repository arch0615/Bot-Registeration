"""
Registration steps for Website #2.
"""

SITE2_STEPS = [
    # ── Page 0: Accept Cookies ─────────────────────────────────────
    {
        "name": "Accept Cookies",
        "fields": [
            {"csv_col": "", "selector": "button:has-text('Accetta tutti i cookie'), button:has-text('Accetta tutti'), button:has-text('Accept all')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
        "optional": True,
    },
    # ── Page 1: Tax ID (Codice Fiscale) ────────────────────────────
    {
        "name": "Page 1 - Tax ID",
        "fields": [
            {"csv_col": "Tax ID", "selector": "#codiceFiscale, input[name='codiceFiscale'], input[placeholder*='Codice fiscale'], input[formcontrolname='codiceFiscale']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 2: Registration Button ────────────────────────────────
    {
        "name": "Page 2 - Register",
        "fields": [],
        "submit_selector": "button:has-text('REGISTRATI'), button:has-text('Registrati')",
        "wait_after": "",
    },
    # ── Page 3: Credentials ──────────────────────────────────────────
    {
        "name": "Page 3 - Credentials",
        "fields": [
            {"csv_col": "__username__",  "selector": "#username",                              "type": "fill"},
            {"csv_col": "Password",      "selector": "input[formcontrolname='password']",       "type": "fill"},
            {"csv_col": "Email",         "selector": "#email",                                  "type": "fill"},
            {"csv_col": "Telephone",     "selector": "#telefono",                               "type": "fill"},
            {"csv_col": "",              "selector": "mat-checkbox[formcontrolname='maggiorenne']", "type": "check"},
            {"csv_col": "",              "selector": "mat-radio-group[formcontrolname='PEP'] mat-radio-button:first-child", "type": "radio"},
            {"csv_col": "",              "selector": "mat-radio-group[formcontrolname='proseguiRegistrazione'] mat-radio-button:first-child", "type": "radio"},
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 4: Bonus Selection ──────────────────────────────────────
    {
        "name": "Page 4 - Bonus",
        "fields": [
            {"csv_col": "", "selector": "mat-radio-group[formcontrolname='bonus'] app-bonus-item:has-text('Casino') mat-radio-button", "type": "click_first"},
        ],
        "submit_selector": "button[appscrollsection='avanti']",
        "wait_after": "",
    },
    # ── Page 5: Name ─────────────────────────────────────────────────
    {
        "name": "Page 5 - Name",
        "fields": [
            {"csv_col": "First name", "selector": "#nome",    "type": "fill"},
            {"csv_col": "Last name",  "selector": "#cognome", "type": "fill"},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
]
