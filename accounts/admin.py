from django.contrib import admin
from .models import Profile, Arrangement


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "position", "office", "birth_date", "gender")
    search_fields = ("first_name", "last_name", "pin")
    list_filter = ("gender", "position", "office")


@admin.register(Arrangement)
class ArrangementAdmin(admin.ModelAdmin):
    list_display = ("date_create", "profile", "position", "audit_conducting", "audit_purpose",
                    "order_num_date", "order_dates", "audit_address", "on_status", "time_check", "time_not_start",
                    "response_audit")
    search_fields = ("profile", "date_create")
    list_filter = ("date_create", "profile")