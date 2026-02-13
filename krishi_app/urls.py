from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('solutions/', views.solutions, name='solutions'),
    
    # Farmer URLs
    path('add-vegetable/', views.add_vegetable, name='add_vegetable'),
    path('delete-vegetable/<int:pk>/', views.delete_vegetable, name='delete_vegetable'),
    
    # Supplier URLs
    path('supplier/marketplace/', views.supplier_marketplace, name='supplier_marketplace'),
    path('supplier/purchase/<int:pk>/', views.purchase_from_farmer, name='purchase_from_farmer'),
    
    # Customer URLs
    path('customer/marketplace/', views.customer_marketplace, name='customer_marketplace'),
    path('customer/order/<int:pk>/', views.order_from_supplier, name='order_from_supplier'),
]