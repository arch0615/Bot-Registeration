"""
Registration steps for Website #5.
"""
from steps_config import COOKIE_SELECTOR

SITE5_STEPS = [
    # ── Page 0: Accept Cookies ─────────────────────────────────────
    {
        "name": "Accept Cookies",
        "fields": [
            {"csv_col": "", "selector": COOKIE_SELECTOR, "type": "click_first"},
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
            {"csv_col": "__phone_local__",  "selector": "input[name='cellulare'], input[placeholder='Cellulare'], input[type='tel'], input[name='telefono']",  "type": "fill"},
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
            # Gender — custom dropdown, click trigger then select option
            {"csv_col": "__gender__", "selector": "", "type": "gogoal_dropdown",
             "trigger": "gogoal-form-dropdown:has(label:has-text('Genere')) .form-dropdown__trigger",
             "selector_map": {
                 "Maschile": "MASCHIO",
                 "Femminile": "FEMMINA",
             }},
            # Birthday — three separate inputs (day/month/year)
            {"csv_col": "__birth_day__",   "selector": "input[name='dataNascita__date__day']",   "type": "fill"},
            {"csv_col": "__birth_month__", "selector": "input[name='dataNascita__date__month']", "type": "fill"},
            {"csv_col": "__birth_year__",  "selector": "input[name='dataNascita__date__year']",  "type": "fill"},
            # Birth country — already defaults to ITALIA, skip
            # Comune di nascita — autocomplete with ng-select
            {"csv_col": "Comune", "selector": "gogoal-form-autocomplete:has(label:has-text('Comune di nascita')) input[role='combobox'], gogoal-form-autocomplete input[aria-autocomplete='list']", "type": "autocomplete"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 4: Address ──────────────────────────────────────────────
    {
        "name": "Page 4 - Address",
        "fields": [
            # Nazione di residenza — already ITALIA, skip
            {"csv_col": "Address",             "selector": "input[name='indirizzoResidenza']",  "type": "fill"},
            {"csv_col": "ZIP Code (CAP)",      "selector": "input[name='capResidenza']",        "type": "fill"},
            {"csv_col": "City of residence",   "selector": "gogoal-form-autocomplete:has(label:has-text('Comune di residenza')) input[role='combobox']", "type": "autocomplete"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 5: Document ─────────────────────────────────────────────
    {
        "name": "Page 5 - Document",
        "fields": [
            {"csv_col": "__document_type__", "selector": "", "type": "gogoal_dropdown",
             "trigger": "gogoal-form-dropdown:has(label:has-text('Tipo documento')) .form-dropdown__trigger",
             "selector_map": {
                 "Carta d'identita' elettronica": "CARTA DI IDENTITA'",
                 "Carta d'identità elettronica": "CARTA DI IDENTITA'",
                 "Carta d'identita'": "CARTA DI IDENTITA'",
                 "Carta d'identità": "CARTA DI IDENTITA'",
                 "Passaporto": "PASSAPORTO",
                 "Patente": "PATENTE",
                 "Porto d'armi": "PORTO D'ARMI",
             }},
            {"csv_col": "Document number", "selector": "input[name='numeroDocumento']", "type": "fill"},
            {"csv_col": "__issuing_body__", "selector": "", "type": "gogoal_dropdown",
             "trigger": "gogoal-form-dropdown:has(label:has-text('Rilasciato da')) .form-dropdown__trigger",
             "selector_map": {}},
            {"csv_col": "Place of issue", "selector": "gogoal-form-autocomplete:has(label:has-text('Comune di rilascio')) input[role='combobox']", "type": "autocomplete"},
            {"csv_col": "__issue_day__",   "selector": "input[name='dataRilascioDocumento__date__day']",   "type": "fill"},
            {"csv_col": "__issue_month__", "selector": "input[name='dataRilascioDocumento__date__month']", "type": "fill"},
            {"csv_col": "__issue_year__",  "selector": "input[name='dataRilascioDocumento__date__year']",  "type": "fill"},
            {"csv_col": "__expiry_day__",   "selector": "input[name='dataScadenzaDocumento__date__day']",   "type": "fill"},
            {"csv_col": "__expiry_month__", "selector": "input[name='dataScadenzaDocumento__date__month']", "type": "fill"},
            {"csv_col": "__expiry_year__",  "selector": "input[name='dataScadenzaDocumento__date__year']",  "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 6: Credentials ──────────────────────────────────────────
    {
        "name": "Page 6 - Credentials",
        "fields": [
            {"csv_col": "__username__",  "selector": "input[name='username']",        "type": "fill"},
            {"csv_col": "Password",      "selector": "input[name='password']",        "type": "fill"},
            {"csv_col": "Password",      "selector": "input[name='passwordConfirm']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 7: Security Question ────────────────────────────────────
    {
        "name": "Page 7 - Security",
        "fields": [
            {"csv_col": "__security_question_site5__", "selector": "", "type": "gogoal_dropdown",
             "trigger": "gogoal-form-dropdown:has(label:has-text('Domanda segreta')) .form-dropdown__trigger",
             "selector_map": {}},
            {"csv_col": "__security_answer__", "selector": "input[name='securityAnswer']",        "type": "fill"},
            {"csv_col": "__security_answer__", "selector": "input[name='securityAnswerConfirm']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 8: Deposit Limit ────────────────────────────────────────
    {
        "name": "Page 8 - Deposit Limit",
        "fields": [
            {"csv_col": "__deposit_limit_site5__", "selector": "", "type": "gogoal_dropdown",
             "trigger": "gogoal-form-dropdown:has(label:has-text('Deposito massimo')) .form-dropdown__trigger",
             "selector_map": {}},
        ],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 9: Promo Code (skip - just click Continua) ────────────
    {
        "name": "Page 9 - Promo Code",
        "fields": [],
        "submit_selector": "button:has-text('Continua')",
        "wait_after": "",
    },
    # ── Page 10: Terms & Conditions (select all) ─────────────────────
    {
        "name": "Page 10 - Terms",
        "fields": [
            {"csv_col": "", "selector": "label[for='privacyAcceptAll__fake'], input#privacyAcceptAll__fake", "type": "click_first"},
        ],
        "submit_selector": "button:has-text('Registrati')",
        "wait_after": "",
    },
    # ── Post-submit: Dismiss error modal if present ──────────────────
    {
        "name": "Dismiss Error Modal",
        "fields": [
            {"csv_col": "", "selector": ".messagebox__item__footer button:has-text('OK'), .messagebox__item__close", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
        "optional": True,
    },
]
