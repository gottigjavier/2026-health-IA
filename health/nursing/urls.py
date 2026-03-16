from django.urls import path
# import os

from . import views
from .modular_views.rooms import rooms

urlpatterns = [
    path("home", views.home, name="home"),
    path("rooms", rooms, name="rooms"),
    path("initial_load", views.initial_load, name="initial_load"),
    path("occupy_bed", views.occupy_bed, name="occupy_bed"),
    path("edit_bed", views.edit_bed, name="edit_bed"),
    path("vacate_bed", views.vacate_bed, name="vacate_bed"),
    path("answered_call", views.answered_call, name="answered_call"),
    path("close_call", views.close_call, name="close_call"),
    path("new_task", views.new_task, name="new_task"),
    path("edit_task", views.edit_task, name="edit_task"),
    path("delete_task", views.delete_task, name="delete_task"),
]
