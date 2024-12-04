from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CompanyViewSet,
    ProfileViewSet,
    CreditCardViewSet,
    SignUpAPIView,
    ChangePasswordAPIView,
    AccountActivationSentAPIView,
    ActivateAccountAPIView,
    DocumentUploadAPIView,
    GetEngineerId,
    GetPersonId,
    GetCompanyId,
    GetProjectId,
    CompanyCustomerViewSet,
    CompanyEngineerViewSet,
    PersonViewSet,
    EngineerViewSet,
    ManufacturerViewSet,
    ProjectViewSet,
)

router = DefaultRouter()

router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'company-customer', CompanyCustomerViewSet, basename='company-customer')
router.register(r'company-engineer', CompanyEngineerViewSet, basename='company-engineer')
router.register(r'persons', PersonViewSet, basename='persons')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'credit-card', CreditCardViewSet, basename='profile')
router.register(r'engineer', EngineerViewSet, basename='engineer')
router.register(r'manufacturer', ManufacturerViewSet, basename='manufacturer')
router.register(r'project', ProjectViewSet, basename='project')


urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-engineer-id/', GetEngineerId.as_view(), name='get-engineer-id'),
    path('get-project-id/', GetProjectId.as_view(), name='get-project-id'),
    path('get-person-id/', GetPersonId.as_view(), name='get-person-id'),
    path('get-company-id/', GetCompanyId.as_view(), name='get-company-id'),
    path('signup/', SignUpAPIView.as_view(), name='signup'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('account-activation-sent/', AccountActivationSentAPIView.as_view(), name='account_activation_sent'),
    path('activate/<uidb64>/<token>/', ActivateAccountAPIView.as_view(), name='activate_account'),
    path('upload-document/', DocumentUploadAPIView.as_view(), name='upload_document'),
]
urlpatterns += router.urls
