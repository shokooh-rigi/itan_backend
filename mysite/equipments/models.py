from django.db import models

from mysite.core.base_model import BaseModel
from mysite.core.models import Service


class TestSheet(models.Model):
    name = models.CharField(max_length=255, blank=False)
    inheritance = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    sheet_generator = models.BooleanField(default=False)
    flag = models.BooleanField(default=True)
    form_fields = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["priority"]
        verbose_name = 'Test Sheet'
        verbose_name_plural = 'Test Sheet'

    def __str__(self):
        return self.name


class Equipment(BaseModel):
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name='equipments',
    )
    test_sheet = models.ForeignKey(
        TestSheet,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='equipments'
    )
    name = models.CharField(
        max_length=255,
        blank=False
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    estimate_work = models.IntegerField(
        default=10,
        blank=False,
        null=False,
        verbose_name='Estimate Work in Minutes'
    )
    flag = models.BooleanField(
        default=True,
    )
    form_fields = models.JSONField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipments'

    def __str__(self):
        return self.name + ' (' + self.service.name + ')'
