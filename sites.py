"""
Site registry — each site has a name, URL, and registration steps.
"""

from steps_config import REGISTRATION_STEPS as SITE1_STEPS
from steps_site2 import SITE2_STEPS
from steps_site3 import SITE3_STEPS
from steps_site5 import SITE5_STEPS

SITES = {
    "1": {
        "name": "Website #1",
        "url": "https://www.planetwin365.it/area-personale/registrati/",
        "steps": SITE1_STEPS,
    },
    "2": {
        "name": "Website #2",
        "url": "https://www.lottomatica.it/area-personale/registrati/",
        "steps": SITE2_STEPS,
    },
    "3": {
        "name": "Website #3",
        "url": "",
        "steps": SITE3_STEPS,
    },
    "4": {
        "name": "Website #4",
        "url": "",
        "steps": [],
    },
    "5": {
        "name": "Website #5",
        "url": "",
        "steps": SITE5_STEPS,
    },
}
