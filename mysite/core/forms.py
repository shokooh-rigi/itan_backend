from django import forms
from django.contrib.auth.forms import *

from .models import *


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', )

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ChangePassword(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2', )

    def __init__(self, *args, **kwargs):
        super(ChangePassword, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class DocumentForm(forms.ModelForm):
    class Meta:
        model = LicenseFiles
        fields = ('value', )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', )

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('title', 'emp_id', 'tel', 'fax', 'cell', 'e_sign', 'pic', 'wallpaper', 'stamp', )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}


class EmailForm(forms.Form):
    subject = forms.CharField(required=True, label='Subject')
    to_email = forms.CharField(required=True, label='To', help_text="if you want to specify more than one, Separate using Comma ',' character")
    cc = forms.CharField(required=False, label='CC', help_text="if you want to specify more than one, Separate using Comma ',' character")
    email_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.error_messages = {'required': '{fieldname} field is required'.format(fieldname=field.label)}
