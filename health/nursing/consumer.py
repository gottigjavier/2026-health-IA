from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from django.conf import settings
from .modular_views.calls.call_new import new_call
from .ws_auth import (
    extract_token_from_scope,
    authenticate_ws_token,
    WS_CLOSE_CODE_MISSING_TOKEN,
    WS_CLOSE_CODE_INVALID_TOKEN,
)
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class appConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = extract_token_from_scope(self.scope)
        if not token:
            await self.close(code=WS_CLOSE_CODE_MISSING_TOKEN)
            return

        user = authenticate_ws_token(token)
        if user is None:
            await self.close(code=WS_CLOSE_CODE_INVALID_TOKEN)
            return

        self.scope["user"] = user
        self.groupname = "appboard"
        await self.channel_layer.group_add(
            self.groupname,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        groupname = getattr(self, "groupname", None)
        if groupname is not None:
            await self.channel_layer.group_discard(
                groupname,
                self.channel_name,
            )
        pass
        # await self.disconnect()

    async def receive(self, app_data):
        data = json.loads(app_data)
        all_data = data["all_data"]
        await self.channel_layer.group_send(
            self.groupname,
            {
                "type": "deprocessing",
                "all_data": all_data,
            },
        )

    async def deprocessing(self, event):
        all_app_data = event["all_data"]
        try:
            logger.info(
                "appConsumer.deprocessing sending payload with beds=%d calls=%d tasks=%d",
                len(all_app_data.get("beds", [])),
                len(all_app_data.get("calls", [])),
                len(all_app_data.get("tasks", [])),
            )
        except Exception:
            pass
        await self.send(json.dumps(all_app_data))


class callConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = extract_token_from_scope(self.scope)
        if not token:
            await self.close(code=WS_CLOSE_CODE_MISSING_TOKEN)
            return

        user = authenticate_ws_token(token)
        if user is None:
            await self.close(code=WS_CLOSE_CODE_INVALID_TOKEN)
            return

        self.scope["user"] = user
        self.groupname = "callsboard"
        await self.channel_layer.group_add(
            self.groupname,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        groupname = getattr(self, "groupname", None)
        if groupname is not None:
            await self.channel_layer.group_discard(
                groupname,
                self.channel_name,
            )
        pass
        # await self.disconnect()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("key") != settings.CALL_SECRET_KEY:
            logger.warning(
                "callConsumer: rejected message with invalid key from bed=%s",
                data.get("bed", "<missing>"),
            )
            return

        if ",0" not in data["bed"]:
            data["state"] = True
        else:
            data["state"] = False
        if data["state"] is True:
            key = data["key"]
            state = data["state"]
            bed = data["bed"]
            n_call = await sync_to_async(new_call)(bed)
            call = {"key": key, "state": state, "bed": bed, "call": n_call}
        else:
            key = data["key"]
            state = data["state"]
            bed = data["bed"]
            try:
                from .modular_views.app.app_ws_update import ws_load

                ans_call = await sync_to_async(ws_load)
            except Exception:
                from .modular_views.calls.call_answered import answ_call

                ans_call = await sync_to_async(answ_call)(bed)
            # for dev test usin rooms.js need send parameter bed
            # --> ans_call = await sync_to_async(answ_call)(bed)
            # for prod using only mosquitto just use ws_load
            # --> from .modular_views.app.app_ws_update import ws_load
            # --> ans_call = await sync_to_async(ws_load)
            call = {"key": key, "state": state, "bed": bed, "call": ans_call}
        await self.channel_layer.group_send(
            self.groupname, {"type": "deprocessing", "call": call}
        )

    async def deprocessing(self, event):
        call = event["call"]
        try:
            # log minimal call info
            if isinstance(call, dict):
                logger.info(
                    "callConsumer.deprocessing sending call for bed=%s state=%s",
                    call.get("bed"),
                    call.get("state"),
                )
        except Exception:
            pass
        await self.send(json.dumps(call))


# -------- mqtt ----------------------------------------------

# ------------------------------------------------------------


class taskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = extract_token_from_scope(self.scope)
        if not token:
            await self.close(code=WS_CLOSE_CODE_MISSING_TOKEN)
            return

        user = authenticate_ws_token(token)
        if user is None:
            await self.close(code=WS_CLOSE_CODE_INVALID_TOKEN)
            return

        self.scope["user"] = user
        self.groupname = "tasksboard"
        await self.channel_layer.group_add(
            self.groupname,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        groupname = getattr(self, "groupname", None)
        if groupname is not None:
            await self.channel_layer.group_discard(
                groupname,
                self.channel_name,
            )
        pass
        # await self.disconnect()

    async def receive(self, task_data):
        data = json.loads(task_data)
        tasks_and_beds = data["tasks_and_beds"]
        await self.channel_layer.group_send(
            self.groupname,
            {
                "type": "deprocessing",
                "tasks_and_beds": tasks_and_beds,
            },
        )

    async def deprocessing(self, event):
        tasks_beds = event["tasks_and_beds"]
        try:
            logger.info("taskConsumer.deprocessing sending tasks_and_beds payload")
        except Exception:
            pass
        await self.send(json.dumps(tasks_beds))
