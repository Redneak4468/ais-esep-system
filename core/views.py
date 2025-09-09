from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import ListView

from accounts.models import Profile


@login_required
def dashboard(request):
    return render(request, "core/dashboard.html")


@login_required
def main_menu(request):
    return render(request, "core/main-menu.html")


@login_required
def contacts(request):
    return render(request, "core/contacts.html")


@login_required
def worker_list(request):
    return render(request, "core/empl_list.html")


@login_required
def settings(request):
    return render(request, "core/settings.html")


@login_required
def arrangement(request):
    return render(request, "core/arrangement.html")


class EmployeeListView(ListView):
    model = Profile
    template_name = "core/contacts.html"
    context_object_name = "contacts"


class ProfileListView(ListView):
    model = Profile
    template_name = "core/contacts.html"
    context_object_name = "contacts"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(last_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(mobile_phone__icontains=query) |
                Q(office_phone__icontains=query) |
                Q(internal_number__icontains=query)
            )
        return queryset
