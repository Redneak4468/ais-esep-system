from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from accounts.models import Profile
from core.models import Department, Office, Position


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


class EmployeePhonesListView(ListView):
    model = Department
    template_name = "core/contacts.html"
    context_object_name = "departments"

    def get_queryset(self):
        office_id = self.request.GET.get("office")

        profiles_qs = Profile.objects.select_related("position", "office")
        if office_id:
            profiles_qs = profiles_qs.filter(office_id=office_id)

        positions_qs = Position.objects.prefetch_related(
            Prefetch("profile_set", queryset=profiles_qs)
        )

        return Department.objects.prefetch_related(
            Prefetch("positions", queryset=Position.objects.prefetch_related("profiles"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["offices"] = Office.objects.all()  # для фильтра
        context["selected_office"] = self.request.GET.get("office")
        return context


class ProfileOfficesListView(ListView):
    model = Profile
    template_name = "core/empl_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("office")

        # фильтрация по филиалу
        office_id = self.request.GET.get("office")
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(last_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(email__icontains=query) |
                Q(birth_date__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["offices"] = Office.objects.all()
        context["selected_office"] = self.request.GET.get("office")
        return context


class EmployeeDetailView(DetailView):
    model = Profile
    template_name = "accounts/dashboard_empl.html"  # путь к шаблону
    context_object_name = "employee"
