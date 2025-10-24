from django.urls import path
from . import views
from .views import (EmployeePhonesListView,
                    ProfileOfficesListView,
                    EmployeeDetailView,
                    ArrangementListView,
                    )

urlpatterns = [
    path("", views.main_menu, name="main_menu"),
    path("contacts/", EmployeePhonesListView.as_view(), name="contacts"),
    path("contacts/export/", views.export_contacts_excel, name="contacts_export_excel"),
    path("employee_list/", ProfileOfficesListView.as_view(), name="employees"),
    path("settings/", views.settings, name="settings"),
    path("arrangement/", ArrangementListView.as_view(), name="arrangement"),
    path("arrangement/update/<int:pk>/", views.arrangement_update, name="arrangement_update"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("arrangement/import-day/", views.import_arrangement_day, name="import_arrangement_day"),
    path("arrangement/generate-month/", views.generate_month_view, name="generate_month"),
    path("arrangement/clear-day/", views.clear_arrangement_day, name="clear_arrangement_day"),
    path("arrangement/delete-day/", views.delete_arrangement_day, name="delete_arrangement_day"),
]
