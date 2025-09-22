from django.contrib import admin
from .models import Office, Position, Department


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address")
    search_fields = ("name", "city")
    list_filter = ("name", "city")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "department")
    search_fields = ("department", "title")
    list_filter = ("department",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
