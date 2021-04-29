from django.forms import ModelForm

from .models import Settlement, SettledSchedule, User


class SettlementForm(ModelForm):
    class Meta:
        model = Settlement
        fields = [
            'contractor',
            'settlement_start',
            'settlement_end',
            'fixed_expenses',
            'created_by',
        ]

    def __init__(self, *args, **kwargs):
        super(SettlementForm, self).__init__(*args, **kwargs)
        self.fields['contractor'].queryset = User.objects.filter(profile__status=2)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class SettledScheduleForm(ModelForm):
    class Meta:
        model = SettledSchedule
        fields = [
            'settlement',
            'schedule',
            'settled_value',
        ]

    def __init__(self, *args, **kwargs):
        super(SettledScheduleForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
