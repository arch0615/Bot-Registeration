"""
Registration steps for Website #4 (BetFlag).
All pages after the REGISTRATI click operate inside iframe #IframeSignup.
"""
from steps_config import COOKIE_STEP

SITE4_STEPS = [
    COOKIE_STEP,
    # ── Page 1: Click REGISTRATI (opens modal with iframe) ──────────
    {
        "name": "Page 1 - Click REGISTRATI",
        "fields": [
            {"csv_col": "", "selector": "#btnSignUp, input[value='REGISTRATI']", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "#IframeSignup",
    },
    # ── Page 2: Select Classica (inside iframe) ───────────────────────
    {
        "name": "Page 2 - Select Classica",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "", "selector": "#ContentPlaceHolder1_ClassicChoice", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "#TextBoxName, input[name*='TextBoxName'], input[name*='codiceFiscale']",
    },
    # ── Page 3: Personal Info + Bonus ──────────────────────────────
    {
        "name": "Page 3 - Personal Info & Bonus",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "First name",  "selector": "#TextBoxName, input[name*='TextBoxName']",     "type": "fill"},
            {"csv_col": "Last name",   "selector": "#TextBoxSurname, input[name*='TextBoxSurname']", "type": "fill"},
            {"csv_col": "Tax ID",      "selector": "#InputCheckCFField, input[name*='InputCheckCF']", "type": "fill"},
            {"csv_col": "",            "selector": "#btnGroupDrop2, .sceltabonusfield button.dropdown-toggle", "type": "click_first"},
            {"csv_col": "",            "selector": "a.dropdown-item:has-text('1.500'), a.dropdown-item:has-text('Slot')", "type": "click_first"},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 4: Choose Upload Method (Standard/Manual) ──────────────
    {
        "name": "Page 4 - Choose Upload Method",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "", "selector": "#ContentPlaceHolder1_btnStandard, a.upload-method-link:has-text('Carica il tuo documento')", "type": "click_first"},
        ],
        "submit_selector": "",
        "wait_after": "input[type='file'], input[name*='fronte']",
    },
    # ── Page 5: Document Upload ────────────────────────────────────
    {
        "name": "Page 5 - Document Upload",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "Front image", "selector": "#upload1", "type": "file_upload"},
            {"csv_col": "Back image",  "selector": "#upload2",  "type": "file_upload"},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 6: Address + Document Details ─────────────────────────
    # BetFlag tries to extract these fields from the uploaded ID document.
    # When extraction succeeds, the page pre-fills some of them (often
    # province, document type, release authority, sometimes the dates and
    # city). `skip_if_filled: True` makes the bot leave any pre-filled
    # value alone and type only into fields that are still empty.
    {
        "name": "Page 6 - Address & Document",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "__province_of_residence_code__", "selector": "#DDLProvinciaResidenzaDomicilio", "type": "select_postback", "skip_if_filled": True},
            {"csv_col": "City of residence",   "selector": "#DDLComuneResidenza",    "type": "select_label", "skip_if_filled": True},
            {"csv_col": "ZIP Code (CAP)",      "selector": "#CapResidenza",           "type": "fill", "skip_if_filled": True},
            {"csv_col": "Address",             "selector": "#IndirizzoResidenza",     "type": "fill", "skip_if_filled": True},
            {"csv_col": "__house_number__",    "selector": "#NumeroCivicoResidenza",  "type": "fill", "skip_if_filled": True},
            {"csv_col": "Document number",     "selector": "#NumeroDocumento",        "type": "fill", "skip_if_filled": True},
            {"csv_col": "__issue_day__",       "selector": "#DDLGiornoRilascioDoc",   "type": "select", "skip_if_filled": True},
            {"csv_col": "__issue_month__",     "selector": "#DDLMeseRilascioDoc",     "type": "select", "skip_if_filled": True},
            {"csv_col": "__issue_year__",      "selector": "#DDLAnnoRilascioDoc",     "type": "select", "skip_if_filled": True},
            {"csv_col": "__expiry_day__",      "selector": "#DDLGiornoScadenzaDoc",   "type": "select", "skip_if_filled": True},
            {"csv_col": "__expiry_month__",    "selector": "#DDLMeseScadenzaDoc",     "type": "select", "skip_if_filled": True},
            {"csv_col": "__expiry_year__",     "selector": "#DDLAnnoScadenzaDoc",     "type": "select", "skip_if_filled": True},
            {"csv_col": "Place of issue",      "selector": "#LuogoRilascioDoc",       "type": "fill", "skip_if_filled": True},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 7: Email & Phone ──────────────────────────────────────
    {
        "name": "Page 7 - Email & Phone",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "Email",      "selector": "#TextBox4",    "type": "fill"},
            {"csv_col": "Email",      "selector": "#TextBox22",   "type": "fill"},
            {"csv_col": "Telephone",  "selector": "#TextBox12",   "type": "fill_skip_prefix"},
            {"csv_col": "Telephone",  "selector": "#TextBox12BIS","type": "fill_skip_prefix"},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 8: Credentials & Security ─────────────────────────────
    {
        "name": "Page 8 - Credentials & Security",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "Username",  "selector": "#TextBox1",      "type": "fill"},
            {"csv_col": "Password",  "selector": "#Password",      "type": "fill"},
            {"csv_col": "Password",  "selector": "#TextBox10",     "type": "fill"},
            {"csv_col": "",          "selector": "#DropDownList1",  "type": "select", "field_cfg": {"value": "1"}},
            {"csv_col": "",          "selector": "#TextBox3",       "type": "fill",   "field_cfg": {"value": "Piera"}},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 9: Profession & PPE ──────────────────────────────────
    {
        "name": "Page 9 - Profession & PPE",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "", "selector": "#Professioni", "type": "select", "field_cfg": {"value": "23"}},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 10: Terms, Deposit Limit & Confirm ───────────────────
    {
        "name": "Page 10 - Terms & Confirm",
        "iframe": "#IframeSignup",
        "fields": [
            {"csv_col": "", "selector": "#CheckBox2",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox1",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox16", "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox3",  "type": "click_first"},
            {"csv_col": "", "selector": "#DropDownList6", "type": "select", "field_cfg": {"value": "100000"}},
            {"csv_col": "", "selector": "#CheckBox6",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox8",  "type": "click_first"},
            {"csv_col": "", "selector": "#CheckBox14", "type": "click_first"},
        ],
        "submit_selector": "#Button1:visible, input[type='submit'][value='Continua' i]:visible, button:has-text('Continua'):visible",
        "wait_after": "",
    },
    # ── Page 11: Welcome Modal (required) ──────────────────────────
    # BetFlag often renders this modal in the PARENT page (outside
    # #IframeSignup). The runner falls back to the parent page when it
    # cannot see the button inside the iframe.
    {
        "name": "Page 11 - Welcome Modal",
        "iframe": "#IframeSignup",
        "fields": [],
        "submit_selector": (
            "#PrintMessage.show .btn.success:visible, "
            "#PrintMessageType .btn.success:visible, "
            "#PrintMessage.show button:has-text('Continua'):visible, "
            ".modal.show button:has-text('Continua'):visible, "
            ".modal.show a:has-text('Continua'):visible, "
            ".modal.show button:has-text('OK'):visible, "
            "#popup-container button:has-text('Continua'):visible"
        ),
        "wait_after": "",
    },
    # ── Page 12: Spending Limit Agreement Modal (required) ─────────
    {
        "name": "Page 12 - Agreement Modal",
        "iframe": "#IframeSignup",
        "fields": [],
        "submit_selector": (
            "#ContentPlaceHolder1_BtnAccept:visible, "
            "#popup-container #ContentPlaceHolder1_BtnAccept, "
            "#popup-container input[value='Accetta' i]:visible, "
            "#popup-container button:has-text('Accetta'):visible, "
            ".modal.show button:has-text('Accetta'):visible, "
            ".modal.show input[value='Accetta' i]:visible"
        ),
        "wait_after": "",
    },
]
