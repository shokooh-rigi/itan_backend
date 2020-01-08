from mysite.core.models import *
from ..estimator.render import *


class CompanySubmittal(models.Model):
    customer = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=False, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=False, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    flag = models.BooleanField(default=True)
    archive = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_on"]
        verbose_name = 'Company Submittal'
        verbose_name_plural = 'Company Submittal'

    def __int__(self):
        return self.id

    @classmethod
    def create_letterhead_pdf(cls, parameters):
        letterhead_pdf = Render.render_to_file('pdfTemplates/submittalTemplate.html', parameters, 'coverletter')
        return letterhead_pdf

    @classmethod
    def delete_letterhead_pdf(cls, parameters):
        delete_pdf = Render.delete_file(parameters, 'letterhead')
        return delete_pdf


class SubmittalForms(models.Model):
    submittal = models.ForeignKey(CompanySubmittal, on_delete=models.CASCADE, blank=False, null=True)
    submittal_form = models.ForeignKey(CompanySubmittalForm, on_delete=models.CASCADE, blank=False)
    ordering = models.IntegerField(blank=False)
    flag = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Submittal Links to Forms'
        verbose_name_plural = 'Submittal Links to Forms'

    def __str__(self):
        return str(self.submittal.id) + " " + self.submittal_form.form_name
