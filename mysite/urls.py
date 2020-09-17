from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from mysite.core import views as core_views
from django.contrib.auth import views
from .core.forms import UserLoginForm
from ajax_select import urls as ajax_select_urls

admin.autodiscover()

urlpatterns = [
    url(r'^ajax_select/', include(ajax_select_urls)),
    path('admin/', admin.site.urls),
    url(r'^accounts/password_change/$', core_views.change_password, name='password_change'),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^$', core_views.home, name='home'),
    url(r'^accounts/signup/$', core_views.signup, name='signup'),
    path('login/', views.LoginView.as_view(template_name="registration/login.html", authentication_form=UserLoginForm), name='login'),
    url(r'^account_activation_sent/$', core_views.account_activation_sent, name='account_activation_sent'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        core_views.activate, name='activate'),
    path('license/upload/', core_views.model_form_upload, name='LicenseInfoFiles'),
    path('profile/', core_views.profile_edit, name='ProfileEdit'),
    path('activities/', core_views.activities, name='Activities'),
    path('djrichtextfield/', include('djrichtextfield.urls')),

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
    path('', include('mysite.schedule.urls')),
    path('', include('mysite.settlement.urls')),
    path('', include('mysite.sheetcreator.urls')),
    path('management/db/', include('mysite.dbmanagement.urls')),
    path('api/', include('api.urls')),
    url(r'^tech/$', core_views.tech, name='Tech'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
