from django import forms


class DateBetweenForm(forms.Form):
    fromDate = forms.DateField(label='From Date', input_formats=['%d/%m/%Y', '%m/%d/%Y', ]
                               , required=True, widget=forms.DateInput(format='%m/%d/%Y'))
    toDate = forms.DateField(label='To Date', input_formats=['%d/%m/%Y', '%m/%d/%Y', ]
                             , required=True, widget=forms.DateInput(format='%m/%d/%Y'))

    def __init__(self, *args, **kwargs):
        super(DateBetweenForm, self).__init__(*args, **kwargs)
        self.fields['fromDate'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['fromDate'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        self.fields['toDate'].widget.attrs['placeholder'] = 'mm/dd/YYYY'
        self.fields['toDate'].widget.attrs['pattern'] = '\d{2}[\/]\d{2}[\/]\d{4}'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
