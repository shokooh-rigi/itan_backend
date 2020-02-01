from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseRedirect
from .forms import CoiForm
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, MEDIA_URL_NOSLASH, WEB_URL, STATIC_URL
from django.core.mail import EmailMessage
from ..core.views import htmlbodytemplate_tag_converter
from .models import Coi
from mysite.core.models import Person, ModulesToEmailTemplateRelation
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def coi_list(request):
    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = 'created_on'

    object_list = Coi.objects.order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    cois = paginator.get_page(page)

    parameters = {'cois': cois,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "coi.html", parameters)


@login_required
def coi_create(request):
    form = CoiForm(request.POST or None, request.FILES or None)
    contractors = Person.objects.filter(company__company_type__name__iexact='mechanical contractor')
    if request.method == 'POST':
        if request.POST.get("truncate"):
            Coi.objects.all().delete()
            return redirect('CoiHome')
        if request.POST.get("cancel"):
            return redirect('CoiHome')
        if form.is_valid():
            if request.POST.get("next"):
                new_coi = form.save()
                to_email = form.cleaned_data['email']
                to_email = to_email.replace(" ", "").replace(";", ",").split(',')
                cc = form.cleaned_data['cc']
                cc = cc.replace(" ", "").replace(";", ",").split(',')
                subject = form.cleaned_data['subject']
                if ModulesToEmailTemplateRelation.objects.filter(module=6).exists():
                    body_content = get_object_or_404(ModulesToEmailTemplateRelation, module=6).template.content
                else:
                    body_content = "There was no email template defined for 'COI'."
                body_content = htmlbodytemplate_tag_converter(2, body_content, request, new_coi)
                if ModulesToEmailTemplateRelation.objects.filter(module=5).exists():
                    footer_content = ModulesToEmailTemplateRelation.objects.get(module=5).template.content
                else:
                    footer_content = "There was no email template defined for 'Email Footer'."
                footer_content = htmlbodytemplate_tag_converter(2, footer_content, request, new_coi)
                message = body_content + '<br />' + footer_content
                if cc != '':
                    email = EmailMessage(
                        subject,
                        message,
                        'estimator@tabtechinc.com',
                        [to_email],
                        cc=[cc]
                    )
                else:
                    email = EmailMessage(
                        subject,
                        message,
                        'estimator@tabtechinc.com',
                        [to_email]
                    )
                email.content_subtype = "html"
                email.send()
                return redirect('CoiHome')
    parameters = {'form': form,
                  'contractors': contractors
                  }
    return render(request, "coiAdd.html", parameters)
