from mysite.order.models import *
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False)
    date_started = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=True)
    date_completed = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=True)
    terms = models.CharField(max_length=255, blank=True)
    description = models.TextField(max_length=255, blank=True)
    percent_of_performance_completed = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100),
                                                                                          MinValueValidator(0)])
    total_payment_received_to_date = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    past_due_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    attention = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    mark_as_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Invoice List'
        verbose_name_plural = 'Invoice List'

    def __str__(self):
        return estimate_number_generator(self.order.proposal.quote.id) + "I"

    @classmethod
    def create_invoice_pdf(cls, parameters):
        quote_pdf = Render.render_to_file('pdfTemplates/invoiceTemplate.html', parameters, 'invoice')
        return quote_pdf

    @classmethod
    def delete_invoice_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'invoice')
        return delete_pdf
