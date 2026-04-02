from django.urls import path
from . import views

urlpatterns = [
    path('marketplace/', views.marketplace, name='marketplace'),
    path('marketplace/product/<int:pk>/', views.product_detail, name='product_detail'),
    path('marketplace/product/<int:pk>/order/', views.place_order, name='place_order'),
    path('farmer/products/', views.my_products, name='my_products'),
    path('farmer/products/add/', views.add_product, name='add_product'),
    path('farmer/orders/', views.incoming_orders, name='incoming_orders'),
    path('farmer/orders/<int:order_id>/', views.manage_order, name='manage_order'),
    path('customer/orders/', views.my_orders, name='my_orders'),
    
    # Cart URLs
    path('cart/', views.view_bulk_cart, name='view_bulk_cart'),
    path('cart/add/<int:pk>/', views.add_to_bulk_cart, name='add_to_bulk_cart'),
    path('cart/item/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/checkout/', views.checkout_bulk_cart, name='checkout_bulk_cart'),
]
