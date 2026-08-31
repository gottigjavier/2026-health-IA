# import pandas as pd
from ..models import Event
from ..utils.dates import dt_now
import logging

logger = logging.getLogger(__name__)


# ------------------ Event ---------------------------------
def save_event(loged_user, action, before, after):
    event = Event()
    try:
        event.loged_user = loged_user
        event.action = action
        event.time = dt_now()
        event.before = before
        event.after = after
        event.save()
        return
    except Exception as e:
        logger.error("Error. Event no saved %s", e)
        return


# ---------------- End of Event ----------------------------


# ---------------- Begin Data Analytics ----------------------------


# ---------------- end Data Analytics ----------------------------
