# ─────────────────────────────────────────────────────────────
#  Registration Bot — Configuration
#  Edit this file to match your site and CSV structure.
# ─────────────────────────────────────────────────────────────

# Path to your CSV file (exported from the CSV Editor, or any .csv)
CSV_FILE = "participants.csv"

# Column name in the CSV that holds the GoLogin profile ID
PROFILE_ID_COLUMN = "profile_id"

# ── Registration page ─────────────────────────────────────────
REGISTRATION_URL = "https://your-site.com/register"

# Map CSV column names → CSS selectors for the form inputs.
# Keys must match your CSV header names exactly (case-sensitive).
FIELD_MAP = {
    "first_name": "#firstName",
    "last_name":  "#lastName",
    "email":      "#email",
    "password":   "#password",
    # "phone":    "#phone",
    # "username": "#username",
    # Add or remove entries to match your form.
}

# CSS selector for the submit button
SUBMIT_SELECTOR = "button[type='submit']"

# CSS selector that appears on the page after a SUCCESSFUL registration.
# The bot waits for this element to confirm the form went through.
SUCCESS_SELECTOR = ".success-message"

# Seconds to wait for the success indicator before marking as FAILED
SUCCESS_TIMEOUT = 15

# ── Timing ────────────────────────────────────────────────────
# Seconds to pause after the GoLogin browser opens (let it settle)
PROFILE_BOOT_WAIT = 3

# Seconds to wait between each registration run
DELAY_BETWEEN_RUNS = 2

# ── GoLogin local API ─────────────────────────────────────────
# The GoLogin desktop app must be running. It exposes a local REST
# API on this port that starts/stops browser profiles.
GOLOGIN_PORT = 36912
