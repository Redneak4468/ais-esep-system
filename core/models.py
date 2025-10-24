from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    name = models.CharField(_("Отдел"), max_length=255)

    def __str__(self):
        return self.name


class Position(models.Model):
    title = models.CharField(_("Название должности"), max_length=150)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="positions",
        null=True, blank=True,
        verbose_name="Отдел"
    )

    def __str__(self):
        return f"{self.title} ({self.department.name})"


class Office(models.Model):
    name = models.CharField(_("Название филиала"), max_length=150)
    city = models.CharField(_("Город"), max_length=100)
    address = models.TextField(_("Адрес"))

    def __str__(self):
        return f"{self.name} ({self.city})"
