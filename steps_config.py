"""
Pre-built step configurations for the registration flow (pages 3–10 + close modal).
Import and assign to settings["steps"] to use.
"""

COOKIE_SELECTOR = (
    "button:has-text('Accetta tutti i cookie'), "
    "button:has-text('Accetta tutti'), "
    "button:has-text('Accept all'), "
    ":is(button, a, div, span):text-is('Accetta'), "
    ":is(button, a, div, span):text-is('ACCETTA'), "
    "#CybsAcceptAllBtn, "
    "#onetrust-accept-btn-handler, "
    "button[id*='accept'], "
    "a.cookie-accept, "
    "[class*='cookie'] button:has-text('Accetta'), "
    "[class*='consent'] button:has-text('Accetta')"
)

COOKIE_STEP = {
    "name": "Accept Cookies",
    "fields": [
        {"csv_col": "", "selector": COOKIE_SELECTOR, "type": "click_first"},
    ],
    "submit_selector": "",
    "wait_after": "",
    "optional": True,
}

REGISTRATION_STEPS = [
    # ── Page 0: Accept Cookies ─────────────────────────────────────
    COOKIE_STEP,
    # ── Page 1: Tax ID (Codice Fiscale) ─────────────────────────────
    {
        "name": "Page 1 - Tax ID",
        "fields": [
            {"csv_col": "Tax ID", "selector": "#codiceFiscale", "type": "fill"},
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 2: Registration Button ────────────────────────────────
    {
        "name": "Page 2 - Register",
        "fields": [],
        "submit_selector": "button:has-text('REGISTRATI')",
        "wait_after": "",
    },
    # ── Page 3: Credentials ──────────────────────────────────────────
    {
        "name": "Page 3 - Credentials",
        "fields": [
            {"csv_col": "__username__",  "selector": "#username",                              "type": "fill"},
            {"csv_col": "Password",      "selector": "input[formcontrolname='password']",       "type": "fill"},
            {"csv_col": "Email",         "selector": "#email",                                  "type": "fill"},
            {"csv_col": "__phone_local__",     "selector": "#telefono",                               "type": "fill"},
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
            {"csv_col": "__bonus_text__", "selector": "__dynamic_bonus__", "type": "click_first"},
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
        "submit_selector": "div.registrati-btn-container button",
        "wait_after": "",
    },
    # ── Page 11: Document Form ───────────────────────────────────────
    {
        "name": "Page 11 - Document Form",
        "fields": [
            {"csv_col": "__document_type__",   "selector": "mat-select[formcontrolname='tipoDocumento']",  "type": "mat_select"},
            {"csv_col": "__issuing_body__",    "selector": "mat-select[formcontrolname='enteRilascio']",   "type": "mat_select"},
            {"csv_col": "Document number",     "selector": "#numeroDocumento",                              "type": "fill"},
            {"csv_col": "Place of issue",      "selector": "#luogoRilascio",                                "type": "autocomplete"},
            {"csv_col": "__issue_date__",      "selector": "#dataEmissione",                                "type": "date"},
            {"csv_col": "__expiration_date__",  "selector": "#dataScadenza",                                "type": "date"},
        ],
        "submit_selector": "button.btn-carica-doc, button:has-text('CARICA DOCUMENTO')",
        "wait_after": "iframe[src*='jumio']",
        "fail_selector": "text=La registrazione non è andata a buon fine",
    },
    # ── Page 12: Jumio - Start ───────────────────────────────────────
    {
        "name": "Page 12 - Jumio Inizia",
        "iframe": "iframe[src*='jumio']",
        "fields": [
            {"csv_col": "", "selector": "button:has-text('Inizia'), button:has-text('INIZIA')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
    },
    # ── Page 13: Jumio - Choose Upload Source ────────────────────────
    {
        "name": "Page 13 - Jumio Caricare il file",
        "iframe": "iframe[src*='jumio']",
        "fields": [
            {"csv_col": "", "selector": "x-ds-card[data-qa-id='upload'], x-ds-card[data-header='Caricare il file']", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "x-file-upload[data-key='FRONTSIDE']",
    },
    # ── Page 14: Jumio - Upload Front ────────────────────────────────
    {
        "name": "Page 14 - Jumio Upload Front",
        "iframe": "iframe[src*='jumio']",
        "fields": [
            {"csv_col": "Front image", "selector": "x-file-upload[data-key='FRONTSIDE'] input[type='file'][data-qa-id='file-browser']", "type": "file_upload"},
        ],
        "submit_selector": "",
        "wait_after": "x-file-upload[data-key='BACKSIDE'][data-enabled='true']",
    },
    # ── Page 15: Jumio - Upload Back ─────────────────────────────────
    {
        "name": "Page 15 - Jumio Upload Back",
        "iframe": "iframe[src*='jumio']",
        "fields": [
            {"csv_col": "Back image", "selector": "x-file-upload[data-key='BACKSIDE'] input[type='file'][data-qa-id='file-browser']", "type": "file_upload"},
        ],
        "submit_selector": "x-ds-button[data-qa-id='continue-button']:not([data-disabled='true'])",
        "wait_after": "button.go-on-btn:not([disabled]):has-text('REGISTRATI')",
    },
    # ── Page 16: Click REGISTRATI (main page) ────────────────────────
    {
        "name": "Page 16 - Registrati",
        "fields": [],
        "submit_selector": "button.go-on-btn:not([disabled]):has-text('REGISTRATI'), button:has-text('REGISTRATI'):not([disabled])",
        "wait_after": "",
    },
]
