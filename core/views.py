import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from datetime import datetime, timedelta, date

from accounts.models import Profile, Arrangement
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
    context_object_name = "departments_data"

    def get_queryset(self):
        office_id = self.request.GET.get("office")
        profiles_qs = Profile.objects.select_related("position", "office")
        query = self.request.GET.get("q")

        if query:
            profiles_qs = profiles_qs.filter(
                Q(last_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(patronymic__icontains=query) |
                Q(phone_number_work__icontains=query) |
                Q(phone_number_government__icontains=query) |
                Q(phone_number_mobile__icontains=query)
            )

        if office_id:
            profiles_qs = profiles_qs.filter(office_id=office_id)

        positions_qs = Position.objects.prefetch_related(
            Prefetch("profiles", queryset=profiles_qs, to_attr="prefetched_profiles")
        )

        departments_qs = Department.objects.prefetch_related(
            Prefetch("positions", queryset=positions_qs, to_attr="prefetched_positions")
        ).order_by("name")

        return departments_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        office_id = self.request.GET.get("office")

        departments_list = []

        for dept in context["departments_data"]:
            employees = []
            for pos in getattr(dept, "prefetched_positions", []):
                for prof in getattr(pos, "prefetched_profiles", []):
                    employees.append({"profile": prof, "position": pos})

            if employees:
                departments_list.append({"dept": dept, "employees": employees})

        context["departments_list"] = departments_list
        context["offices"] = Office.objects.all()
        context["selected_office"] = office_id or ""
        context["query"] = self.request.GET.get("q", "")
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
                Q(email__icontains=query)
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


class ArrangementListView(ListView):
    model = Arrangement
    template_name = "core/arrangement.html"
    context_object_name = "arrangements"
    paginate_by = None

    OFFICE_NAME = "Центральный аппарат"

    def get_selected_date(self):
        """
        Получаем дату из GET-параметра или используем сегодня
        """
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                return timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        return timezone.localdate()

    def get_queryset(self):
        """
        Возвращаем queryset всех записей расстановки на выбранную дату.
        Если таблица не существует — создаём.
        Также проверяем, нет ли новых сотрудников.
        """
        selected_date = self.get_selected_date()
        arrangements = Arrangement.objects.filter(date_create=selected_date)

        existing_profiles = arrangements.values_list("profile_id", flat=True)
        missing_profiles = Profile.objects.filter(office__name="Борбордук аппарат").exclude(id__in=existing_profiles)

        if missing_profiles.exists():
            new_arrs = [
                Arrangement(
                    profile=p,
                    position=p.position,
                    date_create=selected_date,
                )
                for p in missing_profiles
            ]
            Arrangement.objects.bulk_create(new_arrs)
            # обновляем queryset
            arrangements = Arrangement.objects.filter(date_create=selected_date)

        return arrangements.select_related("profile", "position")

    def generate_for_date(self, date_value):
        """Генерация пустых записей для всех сотрудников"""
        employees = Profile.objects.select_related('position').all()
        arrangements = [
            Arrangement(profile=emp, position=emp.position, date_create=date_value)
            for emp in employees
        ]
        Arrangement.objects.bulk_create(arrangements)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_arrangements = self.get_queryset()
        selected_date = self.get_selected_date()

        inspectors = all_arrangements.filter(profile__is_inspector=True)
        apparatus = all_arrangements.filter(profile__is_inspector=False)

        context.update({
            "selected_date": selected_date,
            "inspectors": inspectors.order_by("profile__last_name", "profile__first_name"),
            "apparatus": apparatus.order_by("profile__last_name", "profile__first_name"),
        })
        return context


def arrangement_update(request, pk):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            field = data.get("field")
            value = data.get("value")

            arrangements = Arrangement.objects.get(pk=pk)

            # Проверяем, есть ли такое поле у модели
            if hasattr(arrangements, field):
                setattr(arrangements, field, value)
                arrangements.save(update_fields=[field])
                return JsonResponse({"success": True, "field": field, "value": value})
            else:
                return JsonResponse({"success": False, "error": "Invalid field"})
        except Arrangement.DoesNotExist:
            return JsonResponse({"success": False, "error": "Object not found"})
    return JsonResponse({"success": False, "error": "Invalid request"})


def import_arrangement_day(request):
    """Импорт данных из выбранной даты (копирует все поля в текущий день)"""
    if request.method == "POST":
        source_date = timezone.datetime.fromisoformat(request.POST.get("source_date")).date()
        target_date = timezone.datetime.fromisoformat(request.POST.get("target_date")).date()

        source_records = Arrangement.objects.filter(date_create=source_date)
        if not source_records.exists():
            messages.warning(request, f"Нет данных за {source_date.strftime('%d.%m.%Y')} для импорта.")
            return redirect(f"{reverse('arrangement')}?date={target_date}")

        Arrangement.objects.filter(date_create=target_date).delete()

        new_records = [
            Arrangement(
                profile=rec.profile,
                position=rec.position,
                audit_conducting=rec.audit_conducting,
                audit_purpose=rec.audit_purpose,
                order_num_date=rec.order_num_date,
                order_dates=rec.order_dates,
                audit_address=rec.audit_address,
                on_status=rec.on_status,
                time_check=rec.time_check,
                time_not_start=rec.time_not_start,
                date_create=target_date,
            )
            for rec in source_records
        ]
        Arrangement.objects.bulk_create(new_records)
        messages.success(request,
                         f"Импортировано {len(new_records)} записей из {source_date.strftime('%d.%m.%Y')}.")
        return redirect(f"{reverse('arrangement')}?date={target_date}")


def generate_month_arrangements(year=None, month=None):
    """Генерация записей на месяц"""
    today = timezone.now().date()
    year = year or today.year
    month = month or today.month

    first_day = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)

    employees = Profile.objects.all()
    new_records = []
    current_day = first_day

    while current_day <= last_day:
        for emp in employees:
            if not Arrangement.objects.filter(profile=emp, date_create=current_day).exists():
                new_records.append(Arrangement(profile=emp, position=emp.position, date_create=current_day))
        current_day += timedelta(days=1)

    Arrangement.objects.bulk_create(new_records)
    return len(new_records)


def generate_month_view(request):
    """Создание таблиц за месяц"""
    if request.method == "POST":
        year = int(request.POST.get("year"))
        month = int(request.POST.get("month"))
        created_count = generate_month_arrangements(year, month)
        messages.success(request, f"Создано {created_count} записей за {month:02}.{year}.")
        return redirect("arrangement")


def clear_arrangement_day(request):
    """Очищает данные в таблице за день"""
    if request.method == "POST":
        date_value = timezone.datetime.fromisoformat(request.POST.get("date")).date()
        Arrangement.objects.filter(date_create=date_value).update(
            audit_conducting="",
            audit_purpose="",
            order_num_date="",
            order_dates="",
            audit_address="",
            on_status="",
            time_check="",
            time_not_start="",
        )
        messages.info(request, f"Данные за {date_value.strftime('%d.%m.%Y')} очищены.")
    return redirect(f"{reverse('arrangement')}?date={date_value}")


def delete_arrangement_day(request):
    """Полное удаление таблицы за день"""
    if request.method == "POST":
        date_value = timezone.datetime.fromisoformat(request.POST.get("date")).date()
        Arrangement.objects.filter(date_create=date_value).delete()
        messages.warning(request, f"Таблица за {date_value.strftime('%d.%m.%Y')} удалена.")
    return redirect(f"{reverse('arrangement')}?date={date_value}&auto_create=0")
