from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "position", "office", "birth_date", "gender")
    search_fields = ("first_name", "last_name", "pin")
    list_filter = ("gender", "position", "office")
