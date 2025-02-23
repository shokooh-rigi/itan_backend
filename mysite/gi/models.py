import datetime
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from custom_user.models import User
from mysite.core.base_model import BaseModelWithCreatedByUser, BaseModel
from mysite.core.models import ContactInfo, Setting
from mysite.estimator.models import estimate_number_generator
from mysite.order.models import Order
from mysite.render import Render


class Invoice(BaseModelWithCreatedByUser):
    """
    Represents an invoice for an order. Includes details such as dates,
    description, invoice type, and the associated user who created the invoice.
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        blank=False,
    )
    date_started = models.DateField(blank=True, null=True)
    date_completed = models.DateField(blank=True, null=True)
    terms = models.CharField(max_length=255, blank=True, default="Due upon Receipt")
    description = models.TextField(
        max_length=255, blank=True, default="TESTING AND BALANCING"
    )
    percent_of_performance_completed = models.FloatField(
        default=100, validators=[MaxValueValidator(100), MinValueValidator(0)]
    )
    # Invoice type: 1: Full Invoice, 2: Pre-Demo Invoice, 3: Rest Invoice, 4: DALT
    invoice_type = models.SmallIntegerField(default=1)
    attention = models.CharField(max_length=255, blank=True, null=True)
    edited_on = models.DateField(blank=True, null=True)
    mark_as_paid = models.BooleanField(default=False)
    times_estimate_changed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Invoice List"
        verbose_name_plural = "Invoice Lists"

    def __str__(self):
        return estimate_number_generator(self.order.proposal.estimate.id) + "I"

    @classmethod
    def create_invoice_pdf(cls, parameters):
        """
        Generates a PDF for the invoice using the provided parameters.

        Args:
            parameters (dict): Data to populate the PDF template.

        Returns:
            str: File path of the generated PDF.
        """
        quote_pdf = Render.render_to_file(
            "pdfTemplates/invoiceTemplate.html", parameters, "invoice"
        )
        return quote_pdf

    @classmethod
    def delete_invoice_pdf(cls, parameters):
        """
        Deletes the generated invoice PDF.

        Args:
            parameters (dict): Data to identify the PDF to delete.

        Returns:
            bool: Success of the delete operation.
        """
        delete_pdf = Render.delete_file(parameters, "invoice")
        return delete_pdf

    @property
    def invoice_number(self):
        """
        Generates a formatted invoice number based on the order's project number
        and the invoice ID. The project number is truncated to the first three
        characters, and the invoice ID is zero-padded to three digits.

        Returns:
            str: Formatted invoice number (e.g., "ABC-001").
        """
        return f"{self.order.project_number[:3]}-{self.id:03d}"


class InvoiceTransaction(BaseModelWithCreatedByUser):
    """
    Represents a transaction associated with an invoice.
    Tracks payment details and user who created the transaction.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=False)
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        blank=False,
        null=False,
    )
    payment_date = models.DateField(
        blank=False,
        null=False,
    )
    payment_no = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Invoice Transactions"
        verbose_name_plural = "Invoice Transactions"

    def __str__(self):
        return str(self.invoice) + " $" + str(self.amount)


class AccountSummary(BaseModel):
    """
    Represents a summary of an account, including statements and associated user details.
    """

    customer = models.ForeignKey(
        ContactInfo, on_delete=models.CASCADE, blank=False, null=False
    )
    statement_no = models.CharField(max_length=10, blank=False, null=False)
    total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    attention = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Account Summary List"
        verbose_name_plural = "Account Summary Lists"

    def __str__(self):
        return str(self.statement_no) + " " + str(self.customer)

    @classmethod
    def create_account_summary_pdf(cls, parameters):
        """
        Generates a PDF for the account summary using the provided parameters.

        Args:
            parameters (dict): Data to populate the PDF template.

        Returns:
            str: File path of the generated PDF.
        """
        account_summary_pdf = Render.render_to_file(
            "pdfTemplates/accountSummaryTemplate.html", parameters, "accountsummary"
        )
        return account_summary_pdf

    @classmethod
    def delete_account_summary_pdf(cls, parameters):
        """
        Deletes the generated account summary PDF.

        Args:
            parameters (dict): Data to identify the PDF to delete.

        Returns:
            bool: Success of the delete operation.
        """
        delete_pdf = Render.delete_file(parameters, "accountsummary")
        return delete_pdf


@receiver(post_save, sender=AccountSummary)
def update_statement_number(sender, instance, created, **kwargs):
    """
    Signal handler to update statement numbers after an AccountSummary is created.
    """
    if created:
        last_digit_setting = Setting.objects.get(
            key="Account Summary Number Last Digit"
        )
        last_digit_setting.value = str(int(last_digit_setting.value) + 1)
        last_digit_setting.save()
        instance.statement_no = Setting.objects.get(
            key="Project Number Pre Text"
        ).value.replace("A", "S") + last_digit_setting.value.zfill(3)
        instance.save()


class InvoiceHistory(BaseModel):
    """
    Tracks the history of invoices, including amounts invoiced, paid, and the balance due.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=False)
    total_invoiced = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        blank=False,
        null=False,
    )
    total_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=False,
        null=False,
    )
    balance_due = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=False,
        null=False,
    )
    pdf_filename = models.CharField(
        max_length=50,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ["created_on"]
        verbose_name = "Invoice History"
        verbose_name_plural = "Invoice Histories"

    def __str__(self):
        return str(self.invoice) + ": History " + self.pdf_filename
