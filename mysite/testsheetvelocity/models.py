from mysite.dbmanagement.models import *
import datetime
from mysite.order.models import Order
from mysite.sheetcreator.models import SheetEquipment

# Create your models here.


class VelocityEquipment(models.Model):
    air_moving_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    velocity_data = models.BooleanField(default=False)
    velocity_row = models.SmallIntegerField(default=0)
    velocity_col = models.SmallIntegerField(default=0)

    def __str__(self):
        return str(self.id) + ' ' + str(self.air_moving_equipment)


class VelocitySheetData(models.Model):
    velocity_equipment = models.ForeignKey(VelocityEquipment, on_delete=models.CASCADE, blank=False, null=False)
    sheet_field = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=500, blank=False)

    def __str__(self):
        return str(self.sheet_field) + ' ' + str(self.velocity_equipment)


class VelocitySheetTableData(models.Model):
    velocity_equipment = models.ForeignKey(VelocityEquipment, on_delete=models.CASCADE, blank=False, null=False)
    row = models.SmallIntegerField(blank=False, null=False)
    col = models.SmallIntegerField(blank=False, null=False)
    value = models.CharField(max_length=500, blank=False)

    def __str__(self):
        return str(self.row) + ' ' + str(self.col) + ' ' + str(self.velocity_equipment)
