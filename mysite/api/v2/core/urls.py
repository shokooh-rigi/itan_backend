from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView


from .views import (
    CompanyViewSet,
    EngineerCompanyViewSet,
    HomeView,
    MyTokenObtainPairView,
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
    PersonViewSet,
    ManufacturerViewSet,
    ProjectViewSet,
    CompanyTypeList,
    UserViewSet,
    ServiceViewSet,
    CompanyListView,
    EngineerListAPIView,
    EngineerCreateAPIView,
    EngineerRetrieveAPIView,
    EngineerUpdateAPIView,
    EngineerDestroyAPIView,
)

router = DefaultRouter()

router.register(r"customer", CustomerViewSet, basename="customer")
router.register(r"companies", CompanyViewSet, basename="company")
router.register(
    r"engineer-company", EngineerCompanyViewSet, basename="engineer-company"
)
# router.register(r"user", UserViewSet, basename="user")
# router.register(r"persons", PersonViewSet, basename="persons")
router.register(r"profiles", ProfilesViewSet, basename="profiles")
router.register(r"credit-card", CreditCardViewSet, basename="credit-card")
router.register(r"manufacturer", ManufacturerViewSet, basename="manufacturer")
router.register(r"project", ProjectViewSet, basename="project")
router.register(r"service", ServiceViewSet, basename="service")


urlpatterns = [
    path(
        "profile/",
        ProfileView.as_view(),
        name="profile"
    ),
    path(
        "home/",
        HomeView.as_view(),
        name="home"
    ),
    path(
        "api/token/",
        MyTokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    path(
        "api/token/refresh/",
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
    path(
        "get-company-types/",
        CompanyTypeList.as_view(),
        name="get-company-types"
    ),
    path(
        "signup/",
        SignUpAPIView.as_view(),
        name="signup"
    ),
    path(
        "change-password/",
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
    path(
        "upload-document/",
        DocumentUploadAPIView.as_view(),
        name="upload_document"
    ),
    path(
        "companies/list/",
        CompanyListView.as_view(),
        name="company-list"
    ),
    path(
        "engineer/list/",
        EngineerListAPIView.as_view(),
        name="engineer-list"
    ),
    path(
        "engineer/create/",
        EngineerCreateAPIView.as_view(),
        name="engineer-create"
    ),
    path(
        "engineer/<int:pk>/",
        EngineerRetrieveAPIView.as_view(),
        name="engineer-detail"
    ),
    path(
        "engineer/<int:pk>/update/",
        EngineerUpdateAPIView.as_view(),
        name="engineer-update",
    ),
    path(
        "engineer/<int:pk>/delete/",
        EngineerDestroyAPIView.as_view(),
        name="engineer-delete",
    ),
]
urlpatterns += router.urls
