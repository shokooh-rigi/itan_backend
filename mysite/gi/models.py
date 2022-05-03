from mysite.order.models import *


# Create your models here.


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, blank=False)
    date_started = models.DateField(blank=True, null=True)
    date_completed = models.DateField(blank=True, null=True)
    terms = models.CharField(max_length=255, blank=True, default='Due upon Receipt')
    description = models.TextField(max_length=255, blank=True, default='TESTING AND BALANCING')
    percent_of_performance_completed = models.FloatField(default=100, validators=[MaxValueValidator(100),
                                                                                          MinValueValidator(0)])
    # 1: FUll invoice  2: Pre-Demo Invoice  3: Rest Invoice
    invoice_type = models.SmallIntegerField(default=1)
    attention = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    mark_as_paid = models.BooleanField(default=False)
    times_estimate_changed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Invoice List'
        verbose_name_plural = 'Invoice List'

    def __str__(self):
        return estimate_number_generator(self.order.proposal.quote.estimate.id) + "I"

    @classmethod
    def create_invoice_pdf(cls, parameters):
        quote_pdf = Render.render_to_file('pdfTemplates/invoiceTemplate.html', parameters, 'invoice')
        return quote_pdf

    @classmethod
    def delete_invoice_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'invoice')
        return delete_pdf


class InvoiceTransaction(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=False)
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1)], blank=False, null=False)
    payment_date = models.DateField(default=datetime.datetime.now().strftime("%m/%d/%Y"), blank=False, null=False)
    payment_no = models.CharField(max_length=20, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Invoice Transactions'
        verbose_name_plural = 'Invoice Transactions'

    def __str__(self):
        return str(self.invoice) + ' $' + str(self.amount)


class AccountSummary(models.Model):
    customer = models.ForeignKey(ContactInfo, on_delete=models.CASCADE, blank=False, null=False)
    statement_no = models.CharField(max_length=10, blank=False, null=False)
    total = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    attention = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Account Summary List'
        verbose_name_plural = 'Account Summary List'

    def __str__(self):
        return str(self.statement_no) + ' ' + str(self.customer)

    @classmethod
    def create_account_summary_pdf(cls, parameters):
        account_summary_pdf = Render.render_to_file('pdfTemplates/accountSummaryTemplate.html', parameters, 'accountsummary')
        return account_summary_pdf

    @classmethod
    def delete_account_summary_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'accountsummary')
        return delete_pdf


@receiver(post_save, sender=AccountSummary)
def update_statement_number(sender, instance, created, **kwargs):
    if created:
        new_number = Setting.objects.get(key='Account Summary Number Last Digit')
        new_number.value = int(Setting.objects.get(key='Account Summary Number Last Digit').value) + 1
        new_number.save()
        instance.statement_no = Setting.objects.get(key='Project Number Pre Text').value.replace('A', 'S') + \
                                  Setting.objects.get(key='Account Summary Number Last Digit').value.zfill(3)
        instance.save()


class InvoiceHistory(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=False)
    total_invoiced = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1)], blank=False, null=False)
    total_paid = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], blank=False, null=False)
    balance_due = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], blank=False, null=False)
    pdf_filename = models.CharField(max_length=50, blank=False, null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_on"]
        verbose_name = 'Invoice History'
        verbose_name_plural = 'Invoice History'

    def __str__(self):
        return str(self.invoice) + ': History ' + str(self.pdf_filename)
