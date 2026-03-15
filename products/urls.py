from django.urls import path
from . import views

urlpatterns = [
    path('marketplace/', views.marketplace, name='marketplace'),
    path('marketplace/product/<int:pk>/', views.product_detail, name='product_detail'),
    path('marketplace/product/<int:pk>/order/', views.place_order, name='place_order'),
    path('farmer/products/', views.my_products, name='my_products'),
    path('farmer/products/add/', views.add_product, name='add_product'),
    path('customer/orders/', views.my_orders, name='my_orders'),
]
