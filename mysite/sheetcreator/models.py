from mysite.dbmanagement.models import *
import datetime
from mysite.order.models import Order


class SupplyorReturnChoices(Enum):
    Supply = 1
    Return = 2
    Outside = 3
    Other = 4

    @staticmethod
    def get_items():
        return (
            (SupplyorReturnChoices.Supply.value, 'Supply'),
            (SupplyorReturnChoices.Return.value, 'Return'),
            (SupplyorReturnChoices.Outside.value, 'Outside'),
            (SupplyorReturnChoices.Other.value, 'Other'),
        )

# Create your models here.


class DataSheet(models.Model):
    test_sheet_type = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    sheet_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    system = models.CharField(max_length=50, blank=False)
    number_of_equipment_groups = models.IntegerField(default=1, blank=False)
    archive = models.BooleanField(default=False)

    def __str__(self):
        return self.test_sheet_type.name + " " + self.project.project_number

    class Meta:
        verbose_name = 'VAV & Air Terminal Sheets'
        verbose_name_plural = 'VAV & Air Terminal Sheets'


class DataSheetEquipment(models.Model):
    sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE, blank=False, null=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=True, null=True)
    equipment_group = models.CharField(max_length=50, default='A', blank=False)
    number_of_supply_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    main_data_entry_completed = models.BooleanField(default=False)
    design_data_entry_completed = models.BooleanField(default=False)
    actual_data_entry_completed = models.BooleanField(default=False)
    terminal_design_data_entry_completed = models.BooleanField(default=False)
    terminal_actual_data_entry_completed = models.BooleanField(default=False)

    field_order = models.PositiveIntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return str(self.sheet) + ": " + self.equipment_type.name

    class Meta(object):
        ordering = ['field_order']


class TestSheetGeneralData(models.Model):
    sheet_equipment = models.ForeignKey(DataSheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(TestSheetColumn, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.column_title


class TestSheetData(models.Model):
    data_type = models.PositiveSmallIntegerField(choices=DataTypeChoices.get_items(), default=1, null=False)
    sheet_equipment = models.ForeignKey(DataSheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    sheet_field = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.data_type) + ' ' + str(self.sheet_equipment)


class SheetActualDataCustomField(models.Model):
    test_sheet = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    column_title = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.test_sheet.name + " " + self.column_title


class Sheet(models.Model):
    test_sheet_type = models.ForeignKey(TestSheet, on_delete=models.CASCADE, blank=False, null=False)
    project = models.ForeignKey(Order, on_delete=models.CASCADE, blank=False, null=False)
    sheet_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=True)
    system = models.CharField(max_length=50, blank=False)
    archive = models.BooleanField(default=False)

    def __str__(self):
        return self.test_sheet_type.name + " " + self.project.project_number

    class Meta:
        verbose_name = 'Air Moving Sheets'
        verbose_name_plural = 'Air Moving Sheets'


class SheetEquipment(models.Model):
    sheet = models.ForeignKey(Sheet, on_delete=models.CASCADE, blank=False, null=False)
    equipment_type = models.ForeignKey(Equipment, on_delete=models.CASCADE, blank=False, null=False)
    equipment = models.ForeignKey(EquipmentDb, on_delete=models.CASCADE, blank=True, null=True)
    number_of_supply_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_return_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_outside_air_terminal = models.SmallIntegerField(default=0, blank=False, null=False)
    number_of_any_other = models.SmallIntegerField(default=0, blank=False, null=False)
    main_data_entry_completed = models.BooleanField(default=False)
    design_data_entry_completed = models.BooleanField(default=False)
    actual_data_entry_completed = models.BooleanField(default=False)
    terminal_design_data_entry_completed = models.BooleanField(default=False)
    terminal_actual_data_entry_completed = models.BooleanField(default=False)

    field_order = models.PositiveIntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return str(self.sheet) + ": " + self.equipment_type.name

    class Meta(object):
        ordering = ['field_order']


class SheetEquipmentCommonData(models.Model):
    sheet_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(TestSheetColumn, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.column_title


class SheetEquipmentActualData(models.Model):
    sheet_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(EquipmentCustomField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.equipment_value_name


class SheetEquipmentCustomData(models.Model):
    sheet_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    key = models.ForeignKey(SheetActualDataCustomField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_equipment) + " " + self.key.column_title


class AirTerminalEquipment(models.Model):
    sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE, blank=False, null=False)
    air_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=True, null=True)
    vav_equipment = models.ForeignKey(DataSheetEquipment, on_delete=models.CASCADE, blank=True, null=True)
    code = models.ForeignKey(AirTerminalCode, on_delete=models.CASCADE, blank=True, null=True)
    outlet_no = models.SmallIntegerField(blank=False, null=False)
    type = models.PositiveSmallIntegerField(choices=SupplyorReturnChoices.get_items(), default=1, null=False)
    equipment_name = models.CharField(max_length=255, blank=False, null=True)

    def __str__(self):
        return str(self.sheet) + ": " + str(self.air_equipment) + ": " + str(self.vav_equipment)


class AirTerminalSheetData(models.Model):
    data_type = models.PositiveSmallIntegerField(choices=DataTypeChoices.get_items(), default=1, null=False)
    air_terminal_equipment = models.ForeignKey(AirTerminalEquipment, on_delete=models.CASCADE, blank=False, null=False)
    sheet_field = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.data_type) + ' ' + str(self.air_terminal_equipment)
