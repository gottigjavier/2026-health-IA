import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
import json
from .board import build_board_data

logger = logging.getLogger(__name__)


def ws_load():
    return build_board_data()


def ws_load_encoded():
    data = ws_load()
    return json.dumps(data, sort_keys=True, indent=1, cls=DjangoJSONEncoder)


def app_ws_update():
    all_data = json.loads(ws_load_encoded())
    layer = get_channel_layer()
    # Log payload summary for debugging
    try:
        logger.info(
            "app_ws_update payload: beds=%d calls=%d tasks=%d",
            len(all_data.get("beds", [])),
            len(all_data.get("calls", [])),
            len(all_data.get("tasks", [])),
        )
    except Exception:
        pass

    async_to_sync(layer.group_send)(
        "appboard",
        {
            "type": "deprocessing",
            "all_data": all_data,
        },
    )
