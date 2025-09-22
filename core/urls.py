from django.urls import path
from . import views
from .views import EmployeePhonesListView, ProfileOfficesListView, EmployeeDetailView

urlpatterns = [
    path("", views.main_menu, name="main_menu"),
    path("contacts/", EmployeePhonesListView.as_view(), name="contacts"),
    path("employee_list/", ProfileOfficesListView.as_view(), name="employees"),
    path("settings/", views.settings, name="settings"),
    path("arrangement/", views.arrangement, name="arrangement"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
]
