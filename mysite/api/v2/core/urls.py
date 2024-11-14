from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path

from .views import GetEngineerId, GetPersonId, GetCompanyId, GetProjectId

router = DefaultRouter()
router.register(r'company-customer', views.CompanyCustomerViewSet, basename='company-customer')
router.register(r'company-engineer', views.CompanyEngineerViewSet, basename='company-engineer')
router.register(r'customer', views.CustomerViewSet, basename='customer')
router.register(r'engineer', views.EngineerViewSet, basename='engineer')
router.register(r'manufacturer', views.ManufacturerViewSet, basename='manufacturer')
router.register(r'project', views.ProjectViewSet, basename='project')


urlpatterns = [
    path('get-engineer-id/', GetEngineerId.as_view(), name='get-engineer-id'),
    path('get-project-id/', GetProjectId.as_view(), name='get-project-id'),
    path('get-person-id/', GetPersonId.as_view(), name='get-person-id'),
    path('get-company-id/', GetCompanyId.as_view(), name='get-company-id'),
]
urlpatterns += router.urls
