from .models import Report
from django.forms import ModelForm


class ReportForm(ModelForm):
    class Meta:
        model = Report
        fields = [
            'order',
            'report_date',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}