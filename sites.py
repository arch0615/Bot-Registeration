"""
Site registry — each site has a name, URL, and registration steps.
"""

from steps_config import REGISTRATION_STEPS as SITE1_STEPS

SITES = {
    "1": {
        "name": "Website #1",
        "url": "https://www.planetwin365.it/area-personale/registrati/",
        "steps": SITE1_STEPS,
    },
    "2": {
        "name": "Website #2",
        "url": "",
        "steps": [],
    },
    "3": {
        "name": "Website #3",
        "url": "",
        "steps": [],
    },
    "4": {
        "name": "Website #4",
        "url": "",
        "steps": [],
    },
    "5": {
        "name": "Website #5",
        "url": "",
        "steps": [],
    },
}
