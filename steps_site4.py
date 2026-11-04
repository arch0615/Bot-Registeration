"""
Registration steps for Website #4 (BetFlag).
"""
from steps_config import COOKIE_STEP

SITE4_STEPS = [
    COOKIE_STEP,
    # ── Step 2: Click REGISTRATI in header ───────────────────────────
    {
        "name": "Page 1 - Click REGISTRATI",
        "fields": [
            {"csv_col": "", "selector": "#btnSignUp, input[value='REGISTRATI'], a.registrati:visible, a:has-text('REGISTRATI'):visible, button:has-text('REGISTRATI'):visible", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "#ContentPlaceHolder1_ClassicChoice, a:has-text('Classica'), input[name*='nome'], input[name*='Nome']",
    },
    # ── Step 3: Select REGISTRAZIONE CLASSICA ─────────────────────────
    {
        "name": "Page 2 - Select Classica Registration",
        "fields": [
            {"csv_col": "", "selector": "#ContentPlaceHolder1_ClassicChoice, a.card-choice:has-text('Classica'), a:has-text('Classica'), a:has-text('REGISTRAZIONE CLASSICA')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "input[name*='nome'], input[name*='Nome'], input[name*='codiceFiscale']",
    },
    # ── Page 2: Personal Info + Bonus ──────────────────────────────
    {
        "name": "Page 2 - Personal Info & Bonus",
        "fields": [
            {"csv_col": "First name",  "selector": "#TextBoxName, input[name*='TextBoxName']",     "type": "fill"},
            {"csv_col": "Last name",   "selector": "#TextBoxSurname, input[name*='TextBoxSurname']", "type": "fill"},
            {"csv_col": "Tax ID",      "selector": "#InputCheckCFField, input[name*='InputCheckCF']", "type": "fill"},
            # Open bonus dropdown then select "1.500€ Slot + 25€ Virtual Games"
            {"csv_col": "",            "selector": "#btnGroupDrop2, .sceltabonusfield button.dropdown-toggle", "type": "click_first"},
            {"csv_col": "",            "selector": "a.dropdown-item:has-text('1.500'), a.dropdown-item:has-text('Slot')", "type": "click_first"},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 3: Choose Upload Method (Standard/Manual) ──────────────
    {
        "name": "Page 3 - Choose Upload Method",
        "fields": [
            {"csv_col": "", "selector": "#ContentPlaceHolder1_btnStandard, a.upload-method-link:has-text('Carica il tuo documento')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "input[type='file'], input[name*='fronte']",
    },
    # ── Page 4: Document Upload ────────────────────────────────────
    {
        "name": "Page 4 - Document Upload",
        "fields": [
            {"csv_col": "Front image", "selector": "#upload1, input.inputfile:first-of-type", "type": "file_upload"},
            {"csv_col": "Back image",  "selector": "#upload2, input.inputfile:last-of-type",  "type": "file_upload"},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 5: Address + Document Details ─────────────────────────
    {
        "name": "Page 5 - Address & Document",
        "fields": [
            # RESIDENZA (Nazione defaults to Italia, skip)
            {"csv_col": "__province_of_residence_code__", "selector": "#DDLProvinciaResidenzaDomicilio", "type": "select_postback"},
            {"csv_col": "City of residence",   "selector": "#DDLComuneResidenza",    "type": "select_label"},
            {"csv_col": "ZIP Code (CAP)",      "selector": "#CapResidenza",           "type": "fill"},
            {"csv_col": "Address",             "selector": "#IndirizzoResidenza",     "type": "fill"},
            {"csv_col": "__house_number__",    "selector": "#NumeroCivicoResidenza",  "type": "fill"},
            # DOCUMENTO (Tipo and Autorità are disabled/auto-filled from upload)
            {"csv_col": "Document number",     "selector": "#NumeroDocumento",        "type": "fill"},
            {"csv_col": "__issue_day__",       "selector": "#DDLGiornoRilascioDoc",   "type": "select"},
            {"csv_col": "__issue_month__",     "selector": "#DDLMeseRilascioDoc",     "type": "select"},
            {"csv_col": "__issue_year__",      "selector": "#DDLAnnoRilascioDoc",     "type": "select"},
            {"csv_col": "__expiry_day__",      "selector": "#DDLGiornoScadenzaDoc",   "type": "select"},
            {"csv_col": "__expiry_month__",    "selector": "#DDLMeseScadenzaDoc",     "type": "select"},
            {"csv_col": "__expiry_year__",     "selector": "#DDLAnnoScadenzaDoc",     "type": "select"},
            {"csv_col": "Place of issue",      "selector": "#LuogoRilascioDoc",       "type": "fill"},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 6: Email & Phone ──────────────────────────────────────
    {
        "name": "Page 6 - Email & Phone",
        "fields": [
            {"csv_col": "Email",      "selector": "#TextBox4",    "type": "fill"},
            {"csv_col": "Email",      "selector": "#TextBox22",   "type": "fill"},
            {"csv_col": "Telephone",  "selector": "#TextBox12",   "type": "fill"},
            {"csv_col": "Telephone",  "selector": "#TextBox12BIS","type": "fill"},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 7: Credentials & Security ─────────────────────────────
    {
        "name": "Page 7 - Credentials & Security",
        "fields": [
            {"csv_col": "Username",  "selector": "#TextBox1",      "type": "fill"},
            {"csv_col": "Password",  "selector": "#Password",      "type": "fill"},
            {"csv_col": "Password",  "selector": "#TextBox10",     "type": "fill"},
            {"csv_col": "",          "selector": "#DropDownList1",  "type": "select", "field_cfg": {"value": "1"}},
            {"csv_col": "",          "selector": "#TextBox3",       "type": "fill",   "field_cfg": {"value": "Piera"}},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 8: Profession & PPE ──────────────────────────────────
    {
        "name": "Page 8 - Profession & PPE",
        "fields": [
            {"csv_col": "", "selector": "#Professioni", "type": "select", "field_cfg": {"value": "23"}},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 9: Terms, Deposit Limit & Confirm ───────────────────
    {
        "name": "Page 9 - Terms & Confirm",
        "fields": [
            # Required checkboxes
            {"csv_col": "", "selector": "#CheckBox2",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox1",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox16", "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox3",  "type": "click_first"},
            # Max weekly deposit: 100.000€
            {"csv_col": "", "selector": "#DropDownList6", "type": "select", "field_cfg": {"value": "100000"}},
            # Consensi - Acconsento for SMS, EMAIL, Profilazione
            {"csv_col": "", "selector": "#CheckBox6",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox8",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox14", "type": "click_first"},
        ],
        "submit_selector": "input[value='CONTINUA'], button:has-text('CONTINUA'), a:has-text('CONTINUA')",
        "wait_after": "",
    },
    # ── Page 10: Welcome Modal ─────────────────────────────────────
    {
        "name": "Page 9 - Welcome",
        "fields": [],
        "submit_selector": "button:has-text('Continua'), a:has-text('Continua')",
        "wait_after": "",
        "optional": True,
    },
    # ── Page 11: Spending Limit ────────────────────────────────────
    {
        "name": "Page 10 - Spending Limit",
        "fields": [],
        "submit_selector": "button:has-text('Accetta'), a:has-text('Accetta'), input[value='Accetta']",
        "wait_after": "",
        "optional": True,
    },
]
