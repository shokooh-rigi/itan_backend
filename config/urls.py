# ruff: noqa
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from mysite.core import views as core_views
from django.contrib.auth import views
from mysite.core.forms import UserLoginForm


urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include("django_select2.urls")),
    path('accounts/password_change/', core_views.change_password, name='password_change'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', core_views.signup, name='signup'),
    path('login/', views.LoginView.as_view(template_name="registration/login.html", authentication_form=UserLoginForm), name='login'),
    path('account_activation_sent/', core_views.account_activation_sent, name='account_activation_sent'),
    path('activate/<slug:uidb64>/<slug:token>/', core_views.activate, name='activate'),
    path('license/upload/', core_views.model_form_upload, name='LicenseInfoFiles'),
    path('profile/', core_views.profile_edit, name='ProfileEdit'),
    path('activities/', core_views.activities, name='Activities'),
    path('djrichtextfield/', include('djrichtextfield.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('ts-setup/', include('mysite.testsheetsetup.urls')),
    path('vbts/', include('mysite.testsheetvavboxtemperatureschedule.urls')),
    path('vbs/', include('mysite.testsheetvavboxschedule.urls')),
    path('primary-heat-exchanger-2/', include('mysite.testsheetphe2.urls')),
    path('pitot-traverse-summary/', include('mysite.testsheetpitottraverse.urls')),
    path('hot-water-boiler/', include('mysite.testsheethotwaterboiler.urls')),
    path('management/db/', include('mysite.dbmanagement.urls')),
    path('section/tech/', core_views.tech, name='Tech'),
    path('section/estimate/', core_views.estimate, name='Estimate'),
    path('section/data/', core_views.data, name='Data'),
    path('section/accounting/', core_views.accounting, name='Accounting'),
    path('section/customer/', core_views.customer, name='Customer'),
    path('section/management/', core_views.management, name='Management'),
    path('tech/', include('mysite.dashboardtech.urls'), name='techPanel'),
    path('equipments/', include('mysite.equipments.urls')),
    path('', core_views.home, name='home'),
    path('', include('mysite.estimator.urls')),
    path('', include('mysite.submittal.urls')),
    path('', include('mysite.mgmreport.urls')),
    path('', include('mysite.order.urls')),
    path('', include('mysite.coi.urls')),
    path('', include('mysite.gi.urls')),
    path('', include('mysite.report.urls')),
    path('', include('mysite.bidfilemgm.urls')),
    path('', include('mysite.ibfm.urls')),
    path('', include('mysite.administrative.urls')),
    path('', include('mysite.scheduler.urls')),
    path('', include('mysite.settlement.urls')),
    path('', include('mysite.techupload.urls')),
    path('', include('mysite.sheetcreator.urls')),
    path('', include('mysite.testsheetvav.urls')),
    path('', include('mysite.testsheetterminal.urls')),
    path('', include('mysite.testsheetvelocity.urls')),
    path('', include('mysite.testsheetflow.urls')),
    path('', include('mysite.testsheetpump.urls')),
    path('', include('mysite.testsheetdalt.urls')),
    path('', include('mysite.testsheetchiller.urls')),
    path('', include('mysite.testsheetvavboxfanheatschedule.urls')),
    path('', include('mysite.testsheetinductionunit.urls')),
    path('', include('mysite.testsheetphe.urls')),
    path('', include('mysite.testsheetairmoving.urls')),
    path('', include('mysite.generatereport.urls')),
    path('', include('mysite.projectprocess.urls')),
    path('', include('mysite.masspayment.urls')),
    path('', include('mysite.jobcosting.urls')),
    path('', include('mysite.companyperformance.urls')),
    path('', include('mysite.revenueperformance.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path('api/', include('api.urls')),
    # DRF auth token
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
