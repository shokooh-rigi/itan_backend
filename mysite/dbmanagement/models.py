from __future__ import unicode_literals
import datetime
from enum import Enum
from django.db import models
from custom_user.models import User
from ..core.models import *

# Enums for `choices` ==================================================================================================


class DataTypeChoices(Enum):
    Design = 1
    Actual = 2

    @staticmethod
    def get_items():
        return (
            (DataTypeChoices.Design.value, 'Design'),
            (DataTypeChoices.Actual.value, 'Actual'),
        )


class FieldTypeChoices(Enum):
    Integer = 1
    Float = 2
    Characters = 3

    @staticmethod
    def get_items():
        return (
            (FieldTypeChoices.Integer.value, 'Integer ex: 1, 2, 3, ...'),
            (FieldTypeChoices.Float.value, 'Float ex: 1.2, 52.75, ...'),
            (FieldTypeChoices.Characters.value, 'Characters ex: mechanical, water based, ...'),
        )


class FieldRangeOrSelectiveChoices(Enum):
    Range = 1
    Selective = 2

    @staticmethod
    def get_items():
        return (
            (FieldRangeOrSelectiveChoices.Range.value, 'Range ex: 150-720'),
            (FieldRangeOrSelectiveChoices.Selective.value, 'Selective ex: 1,2,3'),
        )


class ShowParenthesesChoices(Enum):
    Neither = 1
    Design = 2
    Actual = 3
    Both = 4

    @staticmethod
    def get_items():
        return (
            (ShowParenthesesChoices.Neither.value, 'None'),
            (ShowParenthesesChoices.Design.value, 'In Design Value'),
            (ShowParenthesesChoices.Actual.value, 'In Actual Value'),
            (ShowParenthesesChoices.Both.value, 'In Both Cases'),
        )


class OperandChoices(Enum):
    EqualTo = 1
    GreaterThan = 2
    GreaterOrEqualTo = 3
    SmallerThan = 4
    SmallerOrEqualTo = 5
    AssignTo = 6

    @staticmethod
    def get_items():
        return (
            (OperandChoices.EqualTo.value, 'Equal to'),
            (OperandChoices.GreaterThan.value, 'Greater than'),
            (OperandChoices.GreaterOrEqualTo.value, 'Greater or Equal to'),
            (OperandChoices.SmallerThan.value, 'Smaller than'),
            (OperandChoices.SmallerOrEqualTo.value, 'Smaller or Equal to'),
            (OperandChoices.AssignTo.value, 'Assign to'),
        )


# ======================================================================================================================


class TestSheet(models.Model):
    name = models.CharField(max_length=255, blank=False)
    priority = models.IntegerField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    sheet_generator = models.BooleanField(default=False)
    flag = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority"]
        verbose_name = 'Test Sheet'
        verbose_name_plural = 'Test Sheet'

    def __str__(self):
        return self.name


class TestSheetField(models.Model):
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    field_name = models.CharField(max_length=255, blank=False, verbose_name='Field Name')
    field_type = models.PositiveSmallIntegerField(choices=FieldTypeChoices.get_items(), default=1, null=False)
    field_range_or_selective = models.PositiveSmallIntegerField(choices=FieldRangeOrSelectiveChoices.get_items(),
                                                                default=1, null=False)
    field_range = models.CharField(max_length=50, blank=True, verbose_name='Field Range or Field Selection')
    field_postfix = models.CharField(max_length=20, blank=True, verbose_name='Postfix ex: RPM, V, ...')
    default_value = models.CharField(max_length=50, blank=True)
    show_parentheses = models.PositiveSmallIntegerField(choices=ShowParenthesesChoices.get_items(), default=1,
                                                        null=False)
    show_in_design = models.BooleanField(default=True)
    required_in_design = models.BooleanField(default=False)
    show_in_actual = models.BooleanField(default=True)
    required_in_actual = models.BooleanField(default=False)

    def __str__(self):
        return "[field-" + str(self.id) + "]: " + str(self.field_name)


class TestSheetOperation(models.Model):
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    operation = models.CharField(max_length=255, blank=False, verbose_name='ex: [field-1-design] + [field-2-actual]')
    operand_type = models.PositiveSmallIntegerField(choices=OperandChoices.get_items(), default=1, null=False)
    result_field = models.CharField(max_length=50, blank=False, verbose_name='ex: [field-3-design]')
    apply_on_design = models.BooleanField(default=True)
    apply_on_actual = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)


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


class EquipmentDb(models.Model):
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)
    manufacturer = models.ForeignKey(EquipmentManufacturer, on_delete=models.SET_NULL, blank=True, null=True)
    model_number = models.CharField(max_length=50, blank=True, null=True)
    equipment_submittal = models.FileField(upload_to='uploads/equipmentDb/equipment_submittal', blank=True, null=True)
    image = models.FileField(upload_to='uploads/equipmentDb/image', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)

    class Meta:
        unique_together = ('manufacturer', 'model_number',)
        verbose_name = 'Equipment Database'
        verbose_name_plural = 'Equipment Database'

    def __str__(self):
        return str(self.model_number)


class TestSheetColumn(models.Model):
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    column_title = models.CharField(max_length=50, blank=False)
    required = models.BooleanField(default=False)

    def __str__(self):
        return self.test_sheet.name + " " + self.column_title


class EquipmentDbDesignData(models.Model):
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.equipment) + " " + self.key.field_name


class EquipmentTypeCustomField(models.Model):
    field_name = models.CharField(max_length=255, blank=False, verbose_name='Field Name')
    field_type = models.PositiveSmallIntegerField(choices=FieldTypeChoices.get_items(), default=1, null=False)
    field_range_or_selective = models.PositiveSmallIntegerField(choices=FieldRangeOrSelectiveChoices.get_items(),
                                                                default=1, null=False)
    field_range = models.CharField(max_length=50, blank=True, verbose_name='Field Range if Integer or Float')
    field_postfix = models.CharField(max_length=20, blank=True, verbose_name='Postfix ex: RPM, V, ...')
    default_value = models.CharField(max_length=50, blank=True)
    show_parentheses = models.PositiveSmallIntegerField(choices=ShowParenthesesChoices.get_items(), default=1,
                                                        null=False)
    required_in_design = models.BooleanField(default=False)
    required_in_actual = models.BooleanField(default=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return "[field-" + str(self.id) + "]: " + str(self.field_name)


class EquipmentTypeCustomOperation(models.Model):
    operation = models.CharField(max_length=255, blank=False)
    operand_type = models.PositiveSmallIntegerField(choices=OperandChoices.get_items(), default=1, null=False)
    result_field = models.CharField(max_length=50, blank=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return str(self.id)


class ActualDataCustomOperation(models.Model):
    operation = models.CharField(max_length=255, blank=False)
    operand_type = models.PositiveSmallIntegerField(choices=OperandChoices.get_items(), default=1, null=False)
    result_field = models.CharField(max_length=50, blank=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return str(self.id)


class EquipmentCustomField(models.Model):
    equipment_value_name = models.CharField(max_length=255, blank=False, verbose_name='Field Name')
    company_value = models.CharField(max_length=50, blank=False, verbose_name='Design Value')
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=False, null=False)

    def __str__(self):
        return self.equipment_value_name
