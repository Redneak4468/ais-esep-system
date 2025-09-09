from django.db import models


class Department(models.Model):
    name = models.CharField("Отдел", max_length=255)

    def __str__(self):
        return self.name


class Position(models.Model):
    title = models.CharField("Название должности", max_length=150)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="positions",
        null=True, blank=True,
        verbose_name="Отдел"
    )

    def __str__(self):
        return f"{self.title} ({self.department.name})"


class Office(models.Model):
    name = models.CharField("Название филиала", max_length=150)
    city = models.CharField("Город", max_length=100)
    address = models.TextField("Адрес")

    def __str__(self):
        return f"{self.name} ({self.city})"
