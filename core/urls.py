from django.urls import path
from . import views
from .views import EmployeeListView

urlpatterns = [
    path("", views.main_menu, name="main_menu"),
    path("contacts/", EmployeeListView.as_view(), name="contacts"),
    path("employee_list/", views.worker_list, name="empl_list"),
    path("settings/", views.settings, name="settings"),
    path("arrangement/", views.arrangement, name="arrangement"),
]