"""
Registration steps for Website #4 (BetFlag).
"""

SITE4_STEPS = [
    # ── Page 0: Accept Cookies ─────────────────────────────────────
    {
        "name": "Accept Cookies",
        "fields": [
            {"csv_col": "", "selector": "button:has-text('Accetta tutti i cookie'), button:has-text('Accetta tutti'), button:has-text('Accept all'), button:has-text('ACCETTA')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
        "optional": True,
    },
    # ── Page 1: Select Classica ────────────────────────────────────
    {
        "name": "Page 1 - Select Classica",
        "fields": [
            {"csv_col": "", "selector": "a:has-text('Classica'), button:has-text('Classica'), div:has-text('Classica') >> visible=true", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "",
    },
    # ── Page 2: Personal Info + Bonus ──────────────────────────────
    {
        "name": "Page 2 - Personal Info & Bonus",
        "fields": [
            {"csv_col": "First name",  "selector": "input[name*='nome'], input[name*='Nome']",           "type": "fill"},
            {"csv_col": "Last name",   "selector": "input[name*='cognome'], input[name*='Cognome']",     "type": "fill"},
            {"csv_col": "Tax ID",      "selector": "input[name*='codiceFiscale'], input[name*='codice']", "type": "fill"},
            {"csv_col": "",            "selector": "input[type='radio']:near(:text('1500 slot')), label:has-text('1500 slot'), div:has-text('1500 slot') input[type='radio']", "type": "click_first"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 3: Document Upload ────────────────────────────────────
    {
        "name": "Page 3 - Document Upload",
        "fields": [
            {"csv_col": "Front image", "selector": "input[type='file']:first-of-type, input[name*='fronte'], input[accept*='image']:first-of-type", "type": "file_upload"},
            {"csv_col": "Back image",  "selector": "input[type='file']:last-of-type, input[name*='retro'], input[accept*='image']:last-of-type",   "type": "file_upload"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 4: Address + Document Details ─────────────────────────
    {
        "name": "Page 4 - Address & Document",
        "fields": [
            # RESIDENZA
            {"csv_col": "Nation",              "selector": "select[name*='nazione'], input[name*='nazione']",           "type": "select"},
            {"csv_col": "__province_of_residence__", "selector": "select[name*='provincia'], input[name*='provincia']", "type": "select"},
            {"csv_col": "City of residence",   "selector": "input[name*='comune']",                                     "type": "fill"},
            {"csv_col": "ZIP Code (CAP)",      "selector": "input[name*='cap']",                                        "type": "fill"},
            {"csv_col": "Address",             "selector": "input[name*='indirizzo']",                                   "type": "fill"},
            {"csv_col": "__house_number__",    "selector": "input[name*='civico'], input[name*='numero']",               "type": "fill"},
            # DOCUMENTO
            {"csv_col": "__document_type__",   "selector": "select[name*='tipoDocumento'], select[name*='documento']",   "type": "select"},
            {"csv_col": "Document number",     "selector": "input[name*='numeroDocumento'], input[name*='numDoc']",      "type": "fill"},
            {"csv_col": "__issue_date__",      "selector": "input[name*='dataRilascio'], input[name*='rilascio']",       "type": "fill"},
            {"csv_col": "__expiration_date__",  "selector": "input[name*='dataScadenza'], input[name*='scadenza']",      "type": "fill"},
            {"csv_col": "__issuing_body__",    "selector": "input[name*='autorita'], select[name*='autorita']",          "type": "fill"},
            {"csv_col": "Place of issue",      "selector": "input[name*='localita'], input[name*='luogoRilascio']",     "type": "fill"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 5: Email & Phone ──────────────────────────────────────
    {
        "name": "Page 5 - Email & Phone",
        "fields": [
            {"csv_col": "Email",      "selector": "input[name*='email']:first-of-type, input[name*='Email']:first-of-type",  "type": "fill"},
            {"csv_col": "Email",      "selector": "input[name*='conferma'][name*='email'], input[name*='confermaEmail'], input[name*='email']:last-of-type", "type": "fill"},
            {"csv_col": "Telephone",  "selector": "input[name*='cellulare'], input[name*='telefono'], input[type='tel']",    "type": "fill"},
            {"csv_col": "Telephone",  "selector": "input[name*='conferma'][name*='cellulare'], input[name*='confermaCellulare'], input[name*='conferma'][name*='telefono']", "type": "fill"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 6: Credentials & Security ─────────────────────────────
    {
        "name": "Page 6 - Credentials & Security",
        "fields": [
            {"csv_col": "__username__",                "selector": "input[name*='username'], input[name*='Username']",                    "type": "fill"},
            {"csv_col": "Password",                    "selector": "input[name*='password'], input[type='password']",                     "type": "fill"},
            {"csv_col": "Password",                    "selector": "input[name*='conferma'][name*='assword'], input[name*='reinsert'], input[name*='ripeti']", "type": "fill"},
            {"csv_col": "__security_question_site4__", "selector": "select[name*='domanda'], select[name*='segreta']",                   "type": "select"},
            {"csv_col": "__security_answer_site4__",   "selector": "input[name*='risposta'], input[name*='segreta']:not(select)",        "type": "fill"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 7: Complete Registration ──────────────────────────────
    {
        "name": "Page 7 - Complete Registration",
        "fields": [
            {"csv_col": "__profession_site4__",  "selector": "select[name*='professione'], select[name*='Professione']", "type": "select"},
            {"csv_col": "",                      "selector": "input[value='NO'], input[type='radio']:near(:text('NO')), label:has-text('NO')", "type": "click_first"},
        ],
        "submit_selector": "button:has-text('CONTINUA'), input[value='CONTINUA'], a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 8: Terms & Confirm Registration ───────────────────────
    {
        "name": "Page 8 - Terms & Confirm",
        "fields": [
            {"csv_col": "", "selector": "input[type='checkbox'][name*='maggiorenne'], label:has-text('maggiorenne') input[type='checkbox']", "type": "click_first"},
            {"csv_col": "", "selector": "input[type='checkbox'][name*='contratto'], label:has-text('Contratto') input[type='checkbox']",     "type": "click_first"},
            {"csv_col": "", "selector": "input[type='checkbox'][name*='informativa'], label:has-text('Informativa') input[type='checkbox']", "type": "click_first"},
            {"csv_col": "", "selector": "input[type='checkbox'][name*='cookie'], label:has-text('cookie') input[type='checkbox']",           "type": "click_first"},
            # Consensi - select "Acconsentire" for all
            {"csv_col": "", "selector": "input[type='radio'][value*='cconsen']:near(:text('comunicazioni SMS')), label:has-text('Acconsentire'):near(:text('SMS'))", "type": "click_first"},
            {"csv_col": "", "selector": "input[type='radio'][value*='cconsen']:near(:text('comunicazioni EMAIL')), label:has-text('Acconsentire'):near(:text('EMAIL'))", "type": "click_first"},
            {"csv_col": "", "selector": "input[type='radio'][value*='cconsen']:near(:text('profilazione')), label:has-text('Acconsentire'):near(:text('profilazione'))", "type": "click_first"},
            {"csv_col": "", "selector": "input[type='checkbox']:near(:text('dati sensibili')), label:has-text('dati') input[type='checkbox']", "type": "click_first"},
        ],
        "submit_selector": "button:has-text('CONFERMA REGISTRAZIONE'), input[value*='CONFERMA'], a:has-text('CONFERMA')",
        "wait_after": "",
    },
    # ── Page 9: Welcome Modal ──────────────────────────────────────
    {
        "name": "Page 9 - Welcome",
        "fields": [],
        "submit_selector": "button:has-text('Continua'), a:has-text('Continua')",
        "wait_after": "",
        "optional": True,
    },
    # ── Page 10: Spending Limit ────────────────────────────────────
    {
        "name": "Page 10 - Spending Limit",
        "fields": [],
        "submit_selector": "button:has-text('Accetta'), a:has-text('Accetta'), input[value='Accetta']",
        "wait_after": "",
        "optional": True,
    },
]
