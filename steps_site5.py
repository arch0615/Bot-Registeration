"""
Registration steps for Website #5.
"""

SITE5_STEPS = [
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
    # ── Page 1: Registration Form ──────────────────────────────────
    {
        "name": "Page 1 - Registration",
        "fields": [
            {"csv_col": "First name", "selector": "input[placeholder='Nome'], input[name='nome'], input[formcontrolname='nome']",       "type": "fill"},
            {"csv_col": "Last name",  "selector": "input[placeholder='Cognome'], input[name='cognome'], input[formcontrolname='cognome']", "type": "fill"},
            {"csv_col": "Email",      "selector": "input[placeholder='Email'], input[type='email'], input[name='email']",                "type": "fill"},
            {"csv_col": "Telephone",  "selector": "input[placeholder='+39'], input[type='tel'], input[name='telefono']",                 "type": "fill"},
        ],
        "submit_selector": "button:has-text('Registrati')",
        "wait_after": "",
    },
    # ── Page 2: Tax ID (Codice Fiscale) ────────────────────────────
    {
        "name": "Page 2 - Tax ID",
        "fields": [
            {"csv_col": "Tax ID", "selector": "input[placeholder*='Codice Fiscale'], input[name*='codiceFiscale'], input[formcontrolname*='codiceFiscale']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 3: Personal Data ──────────────────────────────────────
    {
        "name": "Page 3 - Personal Data",
        "fields": [
            {"csv_col": "__gender__",    "selector": "select[name*='genere'], select[formcontrolname*='genere']",  "type": "select"},
            {"csv_col": "__birthday__",  "selector": "input[name*='dataNascita'], input[formcontrolname*='dataNascita']", "type": "date"},
            {"csv_col": "Nation",        "selector": "select[name*='nazione'], select[formcontrolname*='nazione']", "type": "select"},
            {"csv_col": "Comune",        "selector": "input[name*='comune'], input[formcontrolname*='comune']",    "type": "autocomplete"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 4: Address ──────────────────────────────────────────────
    {
        "name": "Page 4 - Address",
        "fields": [
            {"csv_col": "Nation",              "selector": "select[name*='nazioneResidenza'], select[formcontrolname*='nazioneResidenza']", "type": "select"},
            {"csv_col": "Address",             "selector": "input[name*='indirizzo'], input[formcontrolname*='indirizzo']",                 "type": "fill"},
            {"csv_col": "ZIP Code (CAP)",      "selector": "input[name*='cap'], input[formcontrolname*='cap']",                            "type": "fill"},
            {"csv_col": "City of residence",   "selector": "input[name*='comune'], input[formcontrolname*='comune']",                      "type": "autocomplete"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 5: Document ─────────────────────────────────────────────
    {
        "name": "Page 5 - Document",
        "fields": [
            {"csv_col": "__document_type__",   "selector": "select[name*='tipoDocumento'], select[formcontrolname*='tipoDocumento']",  "type": "select"},
            {"csv_col": "Document number",     "selector": "input[name*='numeroDocumento'], input[formcontrolname*='numeroDocumento']", "type": "fill"},
            {"csv_col": "__issuing_body__",    "selector": "select[name*='rilasciato'], select[formcontrolname*='rilasciato']",         "type": "select"},
            {"csv_col": "Place of issue",      "selector": "input[name*='comuneRilascio'], input[formcontrolname*='comuneRilascio']",  "type": "autocomplete"},
            {"csv_col": "__issue_date__",      "selector": "input[name*='dataRilascio'], input[formcontrolname*='dataRilascio']",       "type": "date"},
            {"csv_col": "__expiration_date__",  "selector": "input[name*='dataScadenza'], input[formcontrolname*='dataScadenza']",      "type": "date"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 6: Credentials ──────────────────────────────────────────
    {
        "name": "Page 6 - Credentials",
        "fields": [
            {"csv_col": "__username__",  "selector": "input[name*='username'], input[formcontrolname*='username']",   "type": "fill"},
            {"csv_col": "Password",      "selector": "input[name*='password']:not([name*='ripeti']), input[formcontrolname='password']", "type": "fill"},
            {"csv_col": "Password",      "selector": "input[name*='ripeti'], input[formcontrolname*='ripeti'], input[name*='conferma'], input[formcontrolname*='conferma']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 7: Security Question ────────────────────────────────────
    {
        "name": "Page 7 - Security",
        "fields": [
            {"csv_col": "__security_question_site5__",  "selector": "select[name*='domanda'], select[formcontrolname*='domanda']",  "type": "select"},
            {"csv_col": "__security_answer__",    "selector": "input[name*='risposta']:not([name*='ripeti']), input[formcontrolname*='risposta']:not([formcontrolname*='ripeti'])", "type": "fill"},
            {"csv_col": "__security_answer__",    "selector": "input[name*='ripeti'], input[formcontrolname*='ripeti']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 8: Deposit Limit ────────────────────────────────────────
    {
        "name": "Page 8 - Deposit Limit",
        "fields": [
            {"csv_col": "__deposit_limit_site5__",  "selector": "select[name*='deposito'], select[formcontrolname*='deposito']",  "type": "select"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 9: Promo Code (skip) ────────────────────────────────────
    {
        "name": "Page 9 - Promo Code",
        "fields": [],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 10: Terms & Conditions ──────────────────────────────────
    {
        "name": "Page 10 - Terms",
        "fields": [
            {"csv_col": "", "selector": "label:has-text('Seleziona tutti'), input[type='checkbox']:near(:text('Seleziona tutti'))", "type": "click_first"},
        ],
        "submit_selector": "button:has-text('Registrati')",
        "wait_after": "",
    },
]
