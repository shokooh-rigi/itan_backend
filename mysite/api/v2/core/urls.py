from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CompanyViewSet,
    HomeView,
    ProfileView,
    CreditCardViewSet,
    ProfilesViewSet,
    SignUpAPIView,
    ChangePasswordAPIView,
    AccountActivationSentAPIView,
    ActivateAccountAPIView,
    DocumentUploadAPIView,
    GetEngineerId,
    GetPersonId,
    GetCompanyId,
    GetProjectId,
    CustomerViewSet,
    EngineerViewSet,
    PersonViewSet,
    ManufacturerViewSet,
    ProjectViewSet,
    CompanyTypeList,
    UserViewSet,
    ServiceViewSet, CompanyListView,
)

router = DefaultRouter()

router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"customer", CustomerViewSet, basename="customer")
router.register(r"engineer", EngineerViewSet, basename="engineer")
# router.register(r"user", UserViewSet, basename="user")
# router.register(r"persons", PersonViewSet, basename="persons")
router.register(r"profiles", ProfilesViewSet, basename="profiles")
router.register(r"credit-card", CreditCardViewSet, basename="credit-card")
router.register(r"manufacturer", ManufacturerViewSet, basename="manufacturer")
router.register(r"project", ProjectViewSet, basename="project")
router.register(r"service", ServiceViewSet, basename="service")


urlpatterns = [
    path("profile/",
         ProfileView.as_view(),
         name="profile"
         ),
    path("home/",
         HomeView.as_view(),
         name="home"
         ),
    path("api/token/",
         TokenObtainPairView.as_view(),
         name="token_obtain_pair"
         ),
    path("api/token/refresh/",
         TokenRefreshView.as_view(),
         name="token_refresh"
         ),
    path(
        "get-engineer-id/<str:engineer_name>/",
        GetEngineerId.as_view(),
        name="get-engineer-id",
    ),
    path(
        "get-project-id/<str:project_name>/",
        GetProjectId.as_view(),
        name="get-project-id",
    ),
    path(
        "get-person-id/<str:person_name>/",
        GetPersonId.as_view(),
        name="get-person-id"
    ),
    path("get-company-types/",
         CompanyTypeList.as_view(),
         name="get-company-types"
         ),
    # path("signup/", SignUpAPIView.as_view(), name="signup"),
    path("change-password/",
         ChangePasswordAPIView.as_view(),
         name="change_password"
         ),
    path(
        "account-activation-sent/",
        AccountActivationSentAPIView.as_view(),
        name="account_activation_sent",
    ),
    path(
        "activate/<uidb64>/<token>/",
        ActivateAccountAPIView.as_view(),
        name="activate_account",
    ),
    path("upload-document/",
         DocumentUploadAPIView.as_view(),
         name="upload_document"
         ),
    path("company/list/",
         CompanyListView.as_view(),
         name="company-list"
         ),

]
urlpatterns += router.urls
