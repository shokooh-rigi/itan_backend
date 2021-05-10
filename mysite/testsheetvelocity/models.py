from mysite.dbmanagement.models import *
import datetime
from mysite.order.models import Order
from mysite.sheetcreator.models import SheetEquipment

# Create your models here.


class VelocitySheetData(models.Model):
    air_moving_equipment = models.ForeignKey(SheetEquipment, on_delete=models.CASCADE, blank=False, null=False)
    sheet_field = models.ForeignKey(TestSheetField, on_delete=models.CASCADE, blank=False, null=False)
    value = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return str(self.sheet_field) + ' ' + str(self.air_moving_equipment)
