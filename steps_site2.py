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
    # ── Page 6: Birth & Gender ───────────────────────────────────────
    {
        "name": "Page 6 - Birth & Gender",
        "fields": [
            {"csv_col": "__birthday__",  "selector": "#dataDiNascita",  "type": "date"},
            {"csv_col": "Nation",        "selector": "#nazione",        "type": "autocomplete"},
            {"csv_col": "__province__",  "selector": "#provincia",      "type": "autocomplete"},
            {"csv_col": "Comune",        "selector": "#comune",         "type": "autocomplete"},
            {"csv_col": "__gender__",    "selector": "",                 "type": "radio_map",
             "selector_map": {
                 "Maschile":  "mat-radio-group[formcontrolname='sesso'] mat-radio-button[value='M']",
                 "Femminile": "mat-radio-group[formcontrolname='sesso'] mat-radio-button[value='F']",
             }},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
    # ── Page 7: Address ──────────────────────────────────────────────
    {
        "name": "Page 7 - Address",
        "fields": [
            {"csv_col": "__province_of_residence__",  "selector": "#provinciaResidenza",  "type": "autocomplete"},
            {"csv_col": "City of residence",          "selector": "#comuneResidenza",     "type": "autocomplete"},
            {"csv_col": "Address",                    "selector": "#indirizzoResidenza",   "type": "fill"},
            {"csv_col": "__house_number__",            "selector": "#civicoResidenza",      "type": "fill"},
            {"csv_col": "ZIP Code (CAP)",             "selector": "#capResidenza",          "type": "fill"},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
    # ── Page 8: Security Question ────────────────────────────────────
    {
        "name": "Page 8 - Security",
        "fields": [
            {"csv_col": "__security_question__",  "selector": "#domandaSegreta",  "type": "mat_select"},
            {"csv_col": "__security_answer__",    "selector": "#risposta",         "type": "fill"},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
    # ── Page 9: Spending Limit ───────────────────────────────────────
    {
        "name": "Page 9 - Spending Limit",
        "fields": [
            {"csv_col": "__spending_limit__",  "selector": "mat-select[formcontrolname='limite']",  "type": "mat_select"},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
    # ── Page 10: Terms & Conditions ──────────────────────────────────
    {
        "name": "Page 10 - Terms",
        "fields": [
            {"csv_col": "", "selector": "mat-checkbox:has(label:has-text('Contratto'))",  "type": "check"},
            {"csv_col": "", "selector": "mat-radio-button:has(label:has-text('Accetto')):first-of-type", "type": "radio"},
            {"csv_col": "", "selector": "mat-checkbox:has(label:has-text('trattamento dei dati'))", "type": "check"},
        ],
        "submit_selector": "button.go-on-btn",
        "wait_after": "",
    },
    # ── Page 11: Document ────────────────────────────────────────────
    {
        "name": "Page 11 - Document",
        "fields": [
            {"csv_col": "__document_type__",   "selector": "mat-select[formcontrolname='tipoDocumento']",  "type": "mat_select"},
            {"csv_col": "__issuing_body__",    "selector": "mat-select[formcontrolname='enteRilascio']",   "type": "mat_select"},
            {"csv_col": "Document number",     "selector": "#numeroDocumento",                              "type": "fill"},
            {"csv_col": "Place of issue",      "selector": "#luogoRilascio",                                "type": "fill"},
            {"csv_col": "__issue_date__",      "selector": "#dataEmissione",                                "type": "date"},
            {"csv_col": "__expiration_date__",  "selector": "#dataScadenza",                                "type": "date"},
        ],
        "submit_selector": "button:has-text('REGISTRATI')",
        "wait_after": "",
    },
    # ── Close modal (if present) ─────────────────────────────────────
    {
        "name": "Close Modal",
        "fields": [
            {"csv_col": "", "selector": "button.close, button[aria-label='Close'], .modal button:has-text('Chiudi')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
        "optional": True,
    },
]
