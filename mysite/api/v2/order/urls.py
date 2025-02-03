from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    OrderListAPIView,
    OrderAddAPIView,
    OrderEditAPIView,
    OrderDeleteAPIView,
    OrderArchiveAPIView,
    ChangeOrderView,
    ChangeOrderDeleteAPIView,
    ChangeOrderApproveView,
    TechLabelViewSet,
    ControlSystemAPIView,
    OrderEquipmentSubmittalView,
    OrderFieldDrawingView,
    OrderGeneralNotesView,
    OrderSitePicturesView,
    OrderFullUpdateAPIView, ControlSystemViewSet,
)

router = DefaultRouter()

router.register(r"tech-label", TechLabelViewSet, basename="tech-label")
router.register(r'control-systems', ControlSystemViewSet, basename="control-systems")

urlpatterns = [
    path('orders/',
         OrderListAPIView.as_view(),
         name='order-list'),  # List orders
    path('orders/add/',
         OrderAddAPIView.as_view()
         , name='order-add'),  # Add a new order
    path('orders/edit/<int:order_id>/',
         OrderEditAPIView.as_view(),
         name='order-edit'),  # Edit an existing order
    path('orders/delete/<int:order_id>/',
         OrderDeleteAPIView.as_view(),
         name='order-delete'),  # Delete an order
    path('orders/archive/<int:order_id>/',
         OrderArchiveAPIView.as_view(),
         name='order-archive'),  # Archive an order
    path('orders/<int:order_id>/change/',
         ChangeOrderView.as_view(),
         name='change-order'),  # Create a change order
    path('orders/<int:order_id>/change-orders/<int:change_order_id>/delete/',
         ChangeOrderDeleteAPIView.as_view(),
         name='change-order-delete'),
    path('change-orders/<int:change_order_id>/approve/<str:action>/',
         ChangeOrderApproveView.as_view(),
         name='change-order-approve'),
    path('orders/<int:order_id>/control-system/',
         ControlSystemAPIView.as_view(),
         name='control-system'),  # Handle control system for an order
    path('orders/<int:order_id>/equipment-submittal/',
         OrderEquipmentSubmittalView.as_view(),
         name='order_equipment_submittal'),
    path('orders/<int:order_id>/field-drawing/',
         OrderFieldDrawingView.as_view(),
         name='order-field-drawing'),
    path('orders/<int:order_id>/general-notes/',
         OrderGeneralNotesView.as_view(),
         name='order-general-notes'),
    path('orders/<int:order_id>/site-pictures/',
         OrderSitePicturesView.as_view(),
         name='order-site-pictures'),
    path('orders/<int:order_id>/update/',
         OrderFullUpdateAPIView.as_view(),
         name='order-full-update'),
]
urlpatterns += router.urls
