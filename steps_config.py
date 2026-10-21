"""
Pre-built step configurations for the registration flow (pages 3–10 + close modal).
Import and assign to settings["steps"] to use.
"""

REGISTRATION_STEPS = [
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
            {"csv_col": "", "selector": "mat-radio-group[formcontrolname='bonus'] app-bonus-item:first-child mat-radio-button", "type": "click_first"},
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
            {"csv_col": "__province_of_residence__",  "selector": "",  "type": "autocomplete"},  # TODO
            {"csv_col": "City of residence",          "selector": "",  "type": "autocomplete"},  # TODO
            {"csv_col": "Address",                    "selector": "",  "type": "fill"},          # TODO
            {"csv_col": "__house_number__",            "selector": "",  "type": "fill"},          # TODO
            {"csv_col": "ZIP Code (CAP)",             "selector": "",  "type": "fill"},          # TODO
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 8: Security Question ────────────────────────────────────
    {
        "name": "Page 8 - Security",
        "fields": [
            {"csv_col": "__security_question__",  "selector": "",  "type": "select"},  # TODO
            {"csv_col": "__security_answer__",    "selector": "",  "type": "fill"},    # TODO
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 9: Spending Limit ───────────────────────────────────────
    {
        "name": "Page 9 - Spending Limit",
        "fields": [
            {"csv_col": "__spending_limit__",  "selector": "",  "type": "select"},  # TODO
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Page 10: Terms & Conditions ──────────────────────────────────
    {
        "name": "Page 10 - Terms",
        "fields": [
            {"csv_col": "", "selector": "",  "type": "check"},  # TODO: Contratto checkbox
            {"csv_col": "", "selector": "",  "type": "radio"},  # TODO: Accetto radio
            {"csv_col": "", "selector": "",  "type": "check"},  # TODO: Privacy checkbox
        ],
        "submit_selector": "button:has-text('AVANTI')",
        "wait_after": "",
    },
    # ── Close Jumio Modal ────────────────────────────────────────────
    {
        "name": "Close Jumio Modal",
        "fields": [
            {"csv_col": "", "selector": "",  "type": "click"},  # TODO: X close button selector
        ],
        "submit_selector": "",
        "wait_after": "",
    },
]
