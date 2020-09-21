from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.core.mail import BadHeaderError, EmailMessage
from django.http import HttpResponse, HttpResponseRedirect

from mysite.core.tokens import account_activation_token
from .forms import *
from ..coi.models import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL, DEFAULT_FROM_EMAIL


@login_required
def tech(request):
    return render(request, 'tech.html')


@login_required
def home(request):
    if request.user.profile.user_type > 1:
        return render(request, 'home.html')
    else:
        return redirect("/customer/")


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your Account on Tab Technologies INC.'
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)

            return redirect('account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePassword(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('password_change')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ChangePassword(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })


def account_activation_sent(request):
    return render(request, 'account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        current_site = get_current_site(request)
        subject = 'New Registration on Tab Technologies INC.'
        message = render_to_string('send_alert_to_owner.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        try:
            msg = EmailMessage(
                subject,
                message,
                DEFAULT_FROM_EMAIL,
                ['info@tabtechinc.com'],
            )
            msg.send()
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return render(request, 'account_activation_done.html')
    else:
        return render(request, 'account_activation_invalid.html')


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('ProfileEdit')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'profile.html', {'user_form': user_form, 'profile_form': profile_form})


@login_required
def activities(request):
    logs = LogEntry.objects.exclude(change_message="No fields changed.").order_by('-action_time')[:20]
    logCount = LogEntry.objects.exclude(change_message="No fields changed.").order_by('-action_time')[:20].count()

    return render(request, 'activities.html', {"logs": logs, "logCount": logCount})


def htmlbodytemplate_tag_converter(form_type, content, request, customer):
    if request.user.last_name == '' or request.user.last_name is None:
        user_name = 'TAB Technologies, INC. Operator'
    else:
        user_name = request.user.first_name + " " + request.user.last_name
    if request.user.profile.title == '' or request.user.profile.title is None:
        user_title = 'Estimator'
    else:
        user_title = request.user.profile.title
    if request.user.profile.cell == '' or request.user.profile.cell is None:
        user_cell = ''
    else:
        user_cell = request.user.profile.cell
    if request.user.profile.tel == '' or request.user.profile.tel is None:
        user_tel = LicenseInfo.objects.get(key='OwnerTel').value
    else:
        user_tel = request.user.profile.tel

    if form_type == 1:
        content.__str__() \
            .replace("[customer_contact_person]", customer.name) \
            .replace("[customer_email]", customer.mail) \
            .replace("[customer_company_name]", customer.company.name) \
            .replace("[customer_address_line_1]", customer.company.address_line_1) \
            .replace("[customer_address_line_2]", customer.company.address_line_2) \
            .replace("[customer_city]", customer.company.city) \
            .replace("[customer_state]", customer.company.state) \
            .replace("[customer_zip]", str(customer.company.zip))
    elif form_type == 2:
        content.__str__() \
            .replace("[customer_contact_person]", customer.contract_person_name) \
            .replace("[customer_email]", customer.email) \
            .replace("[customer_company_name]", customer.contractor.company.name) \
            .replace("[customer_address_line_1]", customer.contractor.company.address_line_1) \
            .replace("[customer_address_line_2]", customer.contractor.company.address_line_2) \
            .replace("[customer_city]", customer.contractor.company.city) \
            .replace("[customer_state]", customer.contractor.company.state) \
            .replace("[customer_zip]", str(customer.contractor.company.zip))

    return content.__str__() \
        .replace("[user_name]", user_name) \
        .replace("[user_title]", user_title) \
        .replace("[user_cel]", user_cell) \
        .replace("[user_tel]", user_tel) \
        .replace("[ic_company_name]", InsuranceCompany.objects.get(key='company_name').value.__str__()) \
        .replace("[ic_contact_name]", InsuranceCompany.objects.get(key='contact_name').value.__str__()) \
        .replace("[ic_mail]", InsuranceCompany.objects.get(key='mail').value.__str__()) \
        .replace("[ic_tel]", InsuranceCompany.objects.get(key='tel').value.__str__()) \
        .replace("[ic_fax]", InsuranceCompany.objects.get(key='fax').value.__str__()) \
        .replace("[ic_web]", InsuranceCompany.objects.get(key='web').value.__str__()) \
        .replace("[ic_address_line_1]", InsuranceCompany.objects.get(key='address_line_1').value.__str__()) \
        .replace("[ic_address_line_2]", InsuranceCompany.objects.get(key='address_line_2').value.__str__()) \
        .replace("[ic_city]", InsuranceCompany.objects.get(key='city').value.__str__()) \
        .replace("[ic_state]", InsuranceCompany.objects.get(key='state').value.__str__()) \
        .replace("[ic_zip]", InsuranceCompany.objects.get(key='zip').value.__str__())
