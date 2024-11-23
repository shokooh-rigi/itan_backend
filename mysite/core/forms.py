from django import forms
from django.contrib.auth.forms import *
from django_recaptcha.fields import ReCaptchaField

from mysite.core.models import *


class UserLoginForm(AuthenticationForm):
    # captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = ("username", "password")  # , 'captcha')

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )
    captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "captcha")

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class ChangePassword(PasswordChangeForm):
    class Meta:
        model = User
        fields = (
            "old_password",
            "new_password1",
            "new_password2",
        )

    def __init__(self, *args, **kwargs):
        super(ChangePassword, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = LicenseFiles
        fields = ("value",)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "title",
            "employment_id",
            "contact_info",
            "e_sign",
            "photo",
            "wallpaper",
            "stamp",
        )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class AddressesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "physical_address",
            "billing_address",
        )

    def __init__(self, *args, **kwargs):
        super(AddressesForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }


class EmailForm(forms.Form):
    subject = forms.CharField(required=True, label="Subject")
    to_email = forms.CharField(required=True, label="To")
    cc = forms.CharField(required=False, label="CC")
    email_id = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        for field in self.fields.values():
            field.error_messages = {
                "required": "{fieldname} field is required".format(
                    fieldname=field.label
                )
            }
