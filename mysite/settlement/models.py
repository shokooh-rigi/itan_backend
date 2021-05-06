from django.contrib.humanize.templatetags.humanize import intcomma

from mysite.scheduler.models import *


# Create your models here.

class Settlement(models.Model):
    contractor = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False, related_name='settlement_contractor')
    settlement_start = models.DateTimeField(blank=False, null=True)
    settlement_end = models.DateTimeField(blank=False, null=True)
    fixed_expenses = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.id) + ". " + str(self.contractor)

    @classmethod
    def create_settlement_pdf(cls, parameters):
        settlement_pdf = Render.render_to_file('pdfTemplates/settlementTemplate.html', parameters, 'settlement')
        return settlement_pdf

    @classmethod
    def delete_settlement_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'settlement')
        return delete_pdf


class SettledSchedule(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, blank=False, null=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, blank=True)
    settled_total = models.DecimalField(max_digits=8, decimal_places=2)
    settled_value = models.DecimalField(max_digits=8, decimal_places=2)
    # 0 means Hourly and 1 means By Percentage
    settled_type = models.BooleanField(default=False)
    settled_hours = models.FloatField(default=0)
    previous_payment = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    settle_override = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.schedule) + ": $" + str(intcomma(self.settled_value))


class SettledMaintenances(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, blank=False, null=False)
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, blank=True)
    settled_value = models.DecimalField(max_digits=8, decimal_places=2)
    settled_hours = models.FloatField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.maintenance) + ": $" + str(intcomma(self.settled_value))
