from django.db import models
from mysite.schedule.models import *
from django.contrib.humanize.templatetags.humanize import intcomma


# Create your models here.

class Settlement(models.Model):
    contractor = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id) + ". " + str(self.contractor)


class SettledOrders(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, blank=False, null=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False, null=False)
    settled_value = models.DecimalField(max_digits=8, decimal_places=2)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.order) + ": $" + str(intcomma(self.settled_value))
