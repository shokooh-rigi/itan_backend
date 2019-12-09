from .forms import *
from django.shortcuts import render
from django.views.generic import ListView
from mysite.estimator.models import *
import datetime
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from mysite.estimator.views import estimate_total_calculator


def equipments_list(request):
    equipments = Equipment.objects.all().order_by('service', 'name')

    parameters = {'equipments': equipments,
                  }
    return render(request, "equipmentslist.html", parameters)


def company_list(request):
    contacts = Person.objects.order_by('company__company_type', 'company')

    parameters = {'contacts': contacts
                  }
    return render(request, "companylist.html", parameters)


def projects_list(request):
    projects = Project.objects.order_by('name')

    parameters = {'projects': projects
                  }
    return render(request, "projectslist.html", parameters)
