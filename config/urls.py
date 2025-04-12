# ruff: noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from mysite.core import views as core_views
from mysite.core.forms import UserLoginForm

schema_view = get_schema_view(
    openapi.Info(
        title="iTAB",
        default_version="2.0.0",
        description="schema of iTAB project APIs",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="info@airdec.net"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


if settings.TAB_SYSTEM:
    taburlpatterns = [
        path("orders/", include("mysite.api.v2.order.urls")),
        path("", include("mysite.api.v2.invoice.urls")),
        path("", include("mysite.api.v2.account_summary.urls")),
        path("", include("mysite.api.v2.report.urls")),
        path("", include("mysite.api.v2.settlement.urls")),
        path("", include("mysite.api.v2.scheduler.urls")),
        path("", include("mysite.api.v2.coi.urls")),
        # path("", include("mysite.api.v2.equipment.urls")),
        path("", include("mysite.api.v2.project_process.urls")),
        path("", include("mysite.order.urls")),
        # path('', include('mysite.mgmreport.urls')),
        # path('', include('mysite.gi.urls')),
        # path('', include('mysite.report.urls')),
        # path('', include('mysite.administrative.urls')),
        # path('', include('mysite.scheduler.urls')),
        # path('', include('mysite.settlement.urls')),
        # path('', include('mysite.techupload.urls')),
        path("", include("mysite.sheetcreator.urls")),
        path("", include("mysite.testsheetvav.urls")),
        path("", include("mysite.testsheetterminal.urls")),
        path("", include("mysite.testsheetvelocity.urls")),
        path("", include("mysite.testsheetflow.urls")),
        path("", include("mysite.testsheetpump.urls")),
        path("", include("mysite.testsheetdalt.urls")),
        path("", include("mysite.testsheetchiller.urls")),
        path("", include("mysite.testsheetvavboxfanheatschedule.urls")),
        path("", include("mysite.testsheetinductionunit.urls")),
        path("", include("mysite.testsheetphe.urls")),
        path("", include("mysite.testsheetairmoving.urls")),
        path("", include("mysite.generatereport.urls")),
        # path('', include('mysite.masspayment.urls')),
        # path('', include('mysite.jobcosting.urls')),
        # path('', include('mysite.companyperformance.urls')),
        # path('', include('mysite.revenueperformance.urls')),
    ]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", lambda request: redirect("/admin/login/"), name="login"),
    path("logout/", lambda request: redirect("/admin/logout/"), name="logout"),
    path(
        "account_activation_sent/",
        core_views.account_activation_sent,
        name="account_activation_sent",
    ),
    path("activate/<slug:uidb64>/<slug:token>/", core_views.activate, name="activate"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
    # path("", core_views.home, name="home"),
    path("core/", include("mysite.api.v2.core.urls")),
    path("estimate/", include("mysite.api.v2.estimator.urls")),
    path("proposal/", include("mysite.api.v2.proposal.urls")),
    path("bid/", include("mysite.api.v2.bid.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.TAB_SYSTEM:
    urlpatterns += taburlpatterns
