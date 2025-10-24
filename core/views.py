import json
import openpyxl

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from datetime import datetime, timedelta, date
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from urllib.parse import quote

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

    OFFICE_NAME = "Борбордук аппарат"

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

        central_profiles = Profile.objects.filter(office__name=self.OFFICE_NAME)
        missing_profiles = central_profiles.exclude(id__in=central_profiles)

        if missing_profiles.exists():
            new_records = [
                Arrangement(profile=p, position=p.position, date_create=selected_date)
                for p in missing_profiles
            ]
            Arrangement.objects.bulk_create(new_records)

        return (Arrangement.objects.filter(date_create=selected_date, profile__office__name=self.OFFICE_NAME)
                .select_related("profile", "position"))

    def generate_for_date(self, date_value):
        """Генерация пустых записей для всех сотрудников"""
        employees = Profile.objects.select_related('position').all()
        arrangements = [
            Arrangement(profile=emp, position=emp.position, date_create=date_value)
            for emp in employees
        ]
        Arrangement.objects.bulk_create(arrangements)

        return arrangements.filter(profile__office__name=self.OFFICE_NAME).select_related("profile", "position")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date = self.get_selected_date()
        qs = self.get_queryset()

        context["apparatus"] = qs.filter(profile__is_inspector=False).order_by(
            "profile__last_name", "profile__first_name"
        )
        context["inspectors"] = qs.filter(profile__is_inspector=True).order_by(
            "profile__last_name", "profile__first_name"
        )

        context["selected_date"] = selected_date
        context["previous_date"] = selected_date - timedelta(days=1)
        context["next_date"] = selected_date + timedelta(days=1)

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


def export_contacts_excel(request):
    """Экспорт списка сотрудников в Excel"""
    # Создаем новую книгу
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    offices = (
        Profile.objects.filter(office__isnull=False)
        .select_related("office", "position", "position__department")
        .order_by("office__name", "position__department__name", "last_name")
    )

    # Группируем сотрудников по офисам
    offices_data = {}
    for p in offices:
        offices_data.setdefault(p.office.name, []).append(p)

    border = Border(
        left=Side(border_style="thin", color="000000"),
        right=Side(border_style="thin", color="000000"),
        top=Side(border_style="thin", color="000000"),
        bottom=Side(border_style="thin", color="000000"),
    )

    today_str = timezone.now().strftime("%d.%m.%Y")

    # Заголовки
    for office_name, profiles in offices_data.items():
        ws = wb.create_sheet(title=office_name[:31])  # Excel ограничивает длину имени листа

        # Заголовок
        ws.merge_cells("A1:G1")
        ws["A1"] = (
            "Кыргыз Республикасынын Эсептөө палатасынын "
            f"{office_name} кызматкерлеринин телефондорунун жана отурган кабинеттеринин маалымдамасы"
        )
        ws["A1"].font = Font(name="Times New Roman", size=14, bold=True, color="AA0000")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 40

        # Подзаголовок (дата)
        ws.merge_cells("A2:G2")
        ws["A2"] = f"({timezone.now().strftime('%d.%m.%Y')}-ж. карата)"
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
        ws["A2"].font = Font(name="Times New Roman", size=12, italic=True, color="555555")

        if "Борбордук аппарат" in office_name:
            ws.merge_cells("A3:G3")
            ws["A3"] = (
                "почтанын дареги: 720033, Бишкек ш., Исанов көч., 131, факс: 32 35 11"
            )
            ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
            ws["A3"].font = Font(name="Times New Roman", size=12, italic=True, color="AA0000")
            start_row = 5
        else:
            start_row = 4

        # Заголовки таблицы
        headers = ["№", "Аты-жөнү", "Кызмат орду", "Кызматтык телефон №", "Өкмөттүк №", "Мобилдик телефон №", "Каб. №"]
        ws.append(headers)
        header_row = start_row

        header_fill = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = Font(name="Times New Roman", size=12, bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border

        # Начинаем со строки 5
        row_num = header_row + 1

        departments = {}
        for p in profiles:
            dept_name = p.position.department.name if p.position and p.position.department else "Башка"
            departments.setdefault(dept_name, []).append(p)

        # Добавляем подразделы
        for dept, profs in departments.items():
            ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
            cell = ws.cell(row=row_num, column=1, value=dept)
            cell.font = Font(name="Times New Roman", size=12, bold=True, color="000080")
            cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
            row_num += 1

            for i, p in enumerate(profs, start=1):
                ws.append([
                    i,
                    p.full_name(),
                    p.position.title if p.position else "",
                    p.phone_number_work or "",
                    p.phone_number_government or "",
                    p.phone_number_mobile or "",
                    p.office_number or "",
                ])
                for col in range(1, 8):
                    c = ws.cell(row=row_num, column=col)
                    c.font = Font(name="Times New Roman", size=12)
                    c.border = border
                    c.alignment = Alignment(vertical="center", wrap_text=True)
                row_num += 1

            ws.append([])
            row_num += 1

        # Подгон ширины
        widths = [5, 30, 20, 18, 15, 20, 10]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

    filename = f"Справочник телефонов на {today_str}.xlsx"
    encoded_filename = quote(filename)

    # Отправляем файл пользователю
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    wb.save(response)
    return response
