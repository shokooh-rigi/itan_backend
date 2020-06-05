from django.contrib.auth.forms import *
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from mysite.core.models import *


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'captcha')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ChangePassword(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2',)

    def __init__(self, *args, **kwargs):
        super(ChangePassword, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class DocumentForm(forms.ModelForm):
    class Meta:
        model = LicenseFiles
        fields = ('value',)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name',)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('title', 'emp_id', 'tel', 'fax', 'cell', 'e_sign', 'pic', 'wallpaper', 'stamp',)

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class AddressesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('physical_address_line_1', 'physical_address_line_2', 'physical_city', 'physical_state',
                  'physical_zip', 'billing_address_line_1', 'billing_address_line_2', 'billing_city',
                  'billing_state', 'billing_zip')

    def __init__(self, *args, **kwargs):
        super(AddressesForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class EmailForm(forms.Form):
    subject = forms.CharField(required=True, label='Subject')
    to_email = forms.CharField(required=True, label='To')
    cc = forms.CharField(required=False, label='CC')
    email_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
