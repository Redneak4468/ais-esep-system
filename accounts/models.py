from django.contrib.auth.models import User
from datetime import datetime
from django.core.exceptions import ValidationError
from core.models import Office, Position
from django.db import models


class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('vacation', 'В отпуске'),
        ('fired', 'Уволен'),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="profile", verbose_name="Учётная запись", )

    # ФИО
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    patronymic = models.CharField("Отчество", max_length=100, blank=True, null=True)

    # Данные из паспорта (ИНН -> дата рождения + пол)
    pin = models.CharField("ИНН", max_length=20, unique=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True, )
    gender = models.CharField("Пол", max_length=10, choices=GENDER_CHOICES, blank=True)

    def save(self, *args, **kwargs):
        if self.pin and not self.birth_date:
            try:
                birth_date_str = self.pin[1:9]  # Extract substring from 2nd to 7th character of PIN
                self.birth_date = datetime.strptime(birth_date_str, '%d%m%Y').date()
            except ValueError:
                raise ValidationError("Invalid PIN format for birth date extraction.")

        # Determine gender based on the first digit of PIN
        if self.pin and not self.gender:
            first_digit = int(self.pin[0])
            if first_digit == 1:
                self.gender = 'female'
            elif first_digit == 2:
                self.gender = 'male'
            else:
                raise ValidationError("Invalid first digit in PIN for gender determination.")

        super().save(*args, **kwargs)

    def full_name(self):
        return f"{self.first_name} {self.last_name} {self.patronymic}"

    def clean(self):
        # Additional model-level validation
        if self.pin and len(self.pin) != 14:
            raise ValidationError("PIN must be exactly 14 characters long.")

    # Связи
    position = models.ForeignKey(Position, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name="Должность", related_name="profiles")
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал")

    # Контакты
    email = models.EmailField("Email", blank=True, null=True)
    phone_number_work = models.CharField("Рабочий телефон",
                                         max_length=20, blank=True, null=True, default="-")
    phone_number_mobile = models.CharField("Мобильный телефон",
                                           max_length=20, blank=True, null=True, default="-")
    phone_number_government = models.CharField("Правит. телефон",
                                               max_length=10, blank=True, null=True, default="-")
    office_number = models.CharField("№ кабинета", max_length=5, blank=True, null=True, default="-")

    # Дополнительно
    user_photo = models.ImageField("Фото пользователя", upload_to="user_photos/", blank=True, null=True)
    bio = models.TextField("О себе", blank=True, null=True, default="-")

    # Служебные поля
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default="active")
