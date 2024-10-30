from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EstimateListView, EstimateCreateView, EstimateUpdateView, EstimateDeleteView, EstimateEmailViewSet

router = DefaultRouter()
router.register(r'emails', EstimateEmailViewSet, basename='email')

urlpatterns = [
    path('estimate/get/', EstimateListView.as_view(), name='estimate-list'),
    path('estimate/create/', EstimateCreateView.as_view(), name='estimate-create'),
    path('estimate/update/<int:id>/', EstimateUpdateView.as_view(), name='estimate-update'),
    path('estimate/delete/<int:id>/', EstimateDeleteView.as_view(), name='estimate-delete'),
]
