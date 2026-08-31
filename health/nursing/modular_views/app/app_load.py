from ..tasks.task_ws import tasks_scheduler
from .app_ws_update import app_ws_update
from django.http import JsonResponse
from .board import build_board_data


def load():
    data = build_board_data()
    tasks_scheduler()
    app_ws_update()
    return JsonResponse(data, safe=False)
