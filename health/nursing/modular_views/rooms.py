from django.conf import settings
from django.shortcuts import render

# simulates the call and answer buttons of the rooms
def rooms(request):
    return render(request, "rooms.html", {"CALL_SECRET": settings.CALL_SECRET_KEY})
