import logging

from django.conf import settings
from django.shortcuts import render

logger = logging.getLogger(__name__)


def rooms(request):
    # Generate a JWT for the authenticated user so the legacy simulator
    # (rooms.js) can open the /ws/callData/ WebSocket, which authenticates
    # via ?token=<access> (see consumer.callConsumer.connect / ws_auth.py).
    #
    # Fallback: rooms.js also reads the access_token from localStorage (where
    # the React SPA stores it after /api/auth/login), so the meta tag is only
    # needed when the user reached this page without going through the SPA.
    access_token = None
    if request.user.is_authenticated:
        try:
            from ninja_jwt.tokens import RefreshToken

            access_token = str(RefreshToken.for_user(request.user).access_token)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("rooms: could not mint WS token: %s", exc)

    return render(
        request,
        "rooms.html",
        {"CALL_SECRET": settings.CALL_SECRET_KEY, "ACCESS_TOKEN": access_token},
    )
