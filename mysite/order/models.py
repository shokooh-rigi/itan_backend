import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from mysite.core.models import Person
from mysite.proposal.models import Proposal
from ..core.base_model import BasicModel
from ..core.models import TechLabelModel
from ..render import Render


class ControlSystemManufacturer(BasicModel):
    """
    Represents a manufacturer of control systems.
    """
    manufacturer_name = models.CharField(max_length=30, blank=False, null=False)
    contact_name = models.CharField(max_length=255, blank=True)
    tel = models.CharField(max_length=15, blank=True)
    fax = models.CharField(max_length=15, blank=True)
    mail = models.EmailField(max_length=55, blank=True)
    web = models.CharField(max_length=55, blank=True)

    class Meta:
        ordering = ["manufacturer_name"]

    def __str__(self):
        return self.manufacturer_name


class ControlSystem(BasicModel):
    """
    Represents a control system, including its version and related documentation.
    """
    manufacturer = models.ForeignKey(
        ControlSystemManufacturer,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
    )
    version_number = models.CharField(max_length=30, blank=True, null=True)
    os = models.CharField(max_length=20, blank=True, null=True)
    release_date = models.DateField(
        default=datetime.datetime.now,
        blank=True,
        null=True,
    )
    control_file_url = models.URLField(max_length=255, blank=True, null=True)
    documentation = models.FileField(
        upload_to='uploads/control_system_documentations',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["manufacturer"]

    def __str__(self):
        return f"{self.manufacturer}, {self.version_number}"


class Order(BasicModel):
    """
    Represents an order with details such as project information, control system, and documents.
    """
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        blank=False
    )
    project_number = models.CharField(max_length=10, blank=False, null=False)
    architect_name = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    po_number = models.CharField(max_length=30, blank=False)
    date_po_received = models.DateField(blank=True, null=True)
    estimated_date_of_project = models.DateField(blank=True, null=True)
    final_offset = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    predemo_offset = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    control_system = models.ForeignKey(
        ControlSystem,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    equipment_submittal = models.FileField(
        upload_to='uploads/order_equipment_submittal',
        blank=True,
        null=True
    )
    colored_drawing = models.FileField(
        upload_to='uploads/order_colored_drawing',
        blank=True,
        null=True
    )
    report_colored_drawing = models.FileField(
        upload_to='uploads/order_colored_drawing/report',
        blank=True,
        null=True
    )
    colored_drawing_finalize = models.BooleanField(default=False)
    field_draw = models.FileField(
        upload_to='uploads/field_draw',
        blank=True,
        null=True
    )
    general_notes_and_comments = models.TextField(
        max_length=4096,
        blank=True,
        null=True
    )
    general_notes_and_comments_finalize = models.BooleanField(default=False)
    site_pictures = models.FileField(
        upload_to='uploads/order_site_pictures',
        blank=True,
        null=True
    )
    test_sheets = models.FileField(
        upload_to='uploads/order_test_sheets',
        blank=True,
        null=True
    )
    archive = models.BooleanField(default=False)
    fully_settled = models.BooleanField(default=False)
    order_settled_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100),
                    MinValueValidator(0)
                    ]
    )
    pre_demo_completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100),
                    MinValueValidator(0)
                    ]
    )
    note = models.TextField(max_length=2000, blank=True, null=True)
    partial_job_done = models.BooleanField(default=False)
    state = models.CharField(max_length=30, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-proposal"]
        verbose_name = 'Order List'
        verbose_name_plural = 'Order Lists'

    def __str__(self):
        return self.project_number


@receiver(post_save, sender=Order)
def update_project_number(sender, instance, created, **kwargs):
    """
    Signal to update project number when an order is created.
    """
    if created:
        pass


class ChangeOrder(models.Model):
    """
    Represents a change order linked to an existing order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        blank=False,
        null=True
    )
    co_number = models.CharField(max_length=30, blank=False, null=False)
    date = models.DateField(blank=True, null=True)
    confirmed = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['co_number', 'order']

    def __str__(self):
        return f"Change Order #{self.co_number}"

    @classmethod
    def create_change_order_pdf(cls, parameters):
        """
        Generate a PDF for the change order.
        """
        change_order_pdf = Render.render_to_file(
            'pdfTemplates/changeOrderTemplate.html',
            parameters, 'changeorder'
        )
        return change_order_pdf

    @classmethod
    def delete_change_order_pdf(cls, parameters):
        """
        Delete the PDF for the change order.
        """
        # todo: Dear Reza, please check I import Render correctly?
        delete_pdf = Render.delete_file(
            parameters, 'changeorder'
        )
        return delete_pdf


class ChangeOrderService(BasicModel):
    """
    Represents a service associated with a change order.
    """
    change_order = models.ForeignKey(
        ChangeOrder,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=False
    )
    description = models.TextField(max_length=2000, blank=True, null=True)


class TechLabel(BasicModel):
    """
    Represents a technical label for an order, including drawings and contact information.
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    label_model = models.ForeignKey(
        TechLabelModel,
        on_delete=models.PROTECT,
        blank=False,
        null=False
    )
    detailed_drawing = models.BooleanField(default=False)
    schedule_drawing = models.BooleanField(default=False)
    mechanical_drawing = models.BooleanField(default=False)
    tech_test_sheets = models.BooleanField(default=False)
    point_of_contact_name = models.CharField(max_length=50, blank=True, null=True)
    point_of_contact_cell_phone = models.CharField(max_length=15, blank=True, null=True)
    point_of_contact_office_phone = models.CharField(max_length=15, blank=True, null=True)
    schedule_date = models.DateField(blank=True, null=True)
    tech_notes = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.id}: {self.order}"

    @classmethod
    def create_techlabel_pdf(cls, parameters):
        """
        Generate a PDF for the technical label.
        """
        techlabel_pdf = Render.render_to_file('pdfTemplates/techLabelTemplate.html', parameters, 'techlabel')
        return techlabel_pdf


class TechLabelExtraFields(BasicModel):
    """
    Represents additional fields for a technical label.
    """
    tech_label = models.ForeignKey(
        TechLabel,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    title = models.CharField(max_length=50, blank=False, null=False)
    content = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return f"{self.title}: {self.tech_label}"
