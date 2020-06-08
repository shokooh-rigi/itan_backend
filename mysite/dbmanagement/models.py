from __future__ import unicode_literals
import datetime

from creditcards.models import CardExpiryField
from django.core.validators import MinLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from djrichtextfield.models import RichTextField

from custom_user.models import User
from ..core.models import *


class EquipmentManufacturer(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    web = models.CharField(max_length=55, blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=55, blank=True)
    state = models.CharField(max_length=55, blank=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=False, null=True)
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=255, blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    estimate_work = models.IntegerField(default=10, blank=False, null=False, verbose_name='Estimate Work in Minutes')
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = 'Equipment Type'
        verbose_name_plural = 'Equipment Type'

    def __str__(self):
        return self.name + ' (' + self.service.name + ')'


class EquipmentTypeCustomField(models.Model):
    field_name = models.CharField(max_length=255, blank=False, verbose_name='Field Name')
    FIELD_TYPE_CHOICES = (
        (1, 'Integer ex: 1, 2, 3, ...'),
        (2, 'Float ex: 1.2, 52.75, ...'),
        (3, 'Characters ex: mechanical, water based, ...'),
    )
    field_type = models.PositiveSmallIntegerField(choices=FIELD_TYPE_CHOICES, default=1, null=False)
    FIELD_RANGE_OR_SELECTIVE_CHOICES = (
        (1, 'Range ex: 150-720'),
        (2, 'Selective ex: 1,2,3'),
    )
    field_range_or_selective = models.PositiveSmallIntegerField(choices=FIELD_RANGE_OR_SELECTIVE_CHOICES, default=1, null=False)
    field_range = models.CharField(max_length=50, blank=True, verbose_name='Field Range if Integer or Float')
    field_postfix = models.CharField(max_length=20, blank=True, verbose_name='Postfix ex: RPM, V, ...')
    default_value = models.CharField(max_length=50, blank=True)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return "[field-" + str(self.id) + "]: " + str(self.field_name)


class EquipmentTypeCustomOperation(models.Model):
    operation = models.CharField(max_length=255, blank=False)
    OPERAND_CHOICES = (
        (1, 'Equal to'),
        (2, 'Greater than'),
        (3, 'Greater or Equal to'),
        (4, 'Smaller than'),
        (5, 'Smaller or Equal to'),
    )
    operand_type = models.PositiveSmallIntegerField(choices=OPERAND_CHOICES, default=1, null=False)
    result_field = models.CharField(max_length=50, blank=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return str(self.id)


class EquipmentDb(models.Model):
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)
    manufacturer = models.ForeignKey(EquipmentManufacturer, on_delete=models.SET_NULL, blank=False, null=True)
    model_number = models.CharField(max_length=50, blank=False)
    serial_number = models.CharField(max_length=50, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        unique_together = ('manufacturer', 'model_number',)
        verbose_name = 'Equipment Database'
        verbose_name_plural = 'Equipment Database'

    def __str__(self):
        return str(self.model_number)


class EquipmentCustomField(models.Model):
    equipment_value_name = models.CharField(max_length=255, blank=False, verbose_name='Field Name')
    company_value = models.CharField(max_length=50, blank=False, verbose_name='Design Value')
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return self.equipment_value_name

