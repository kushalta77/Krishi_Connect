from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('farmer/dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('blog/organic-farming-future/', views.blog_organic_future, name='blog_organic_future'),
    path('blog/smart-irrigation/', views.blog_smart_irrigation, name='blog_smart_irrigation'),
    path('blog/climate-change/', views.blog_climate_change, name='blog_climate_change'),
    path('blog/direct-market-access/', views.blog_direct_market, name='blog_direct_market'),
    path('blog/soil-testing/', views.blog_soil_testing, name='blog_soil_testing'),
    path('blog/pest-management/', views.blog_pest_management, name='blog_pest_management'),
    path('blog/crop-rotation/', views.blog_crop_rotation, name='blog_crop_rotation'),
    path('organic-crops/', views.organic_crops, name='organic_crops'),
    path('solutions/', views.solutions, name='solutions'),
    path('solutions/smart-farming/', views.smart_farming, name='smart_farming'),
    path('solutions/market-intelligence/', views.market_intelligence, name='market_intelligence'),
    path('solutions/supply-chain/', views.supply_chain, name='supply_chain'),
    path('solutions/expert-advisory/', views.expert_advisory, name='expert_advisory'),
    
    # Farmer URLs
    path('farmer/products/', views.farmer_products, name='farmer_products'),
    path('farmer/stock/', views.farmer_stock, name='farmer_stock'),
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    path('add-vegetable/', views.add_vegetable, name='add_vegetable'),
    path('edit-vegetable/<int:pk>/', views.edit_vegetable, name='edit_vegetable'),
    path('view-vegetable/<int:pk>/', views.view_vegetable, name='view_vegetable'),
    path('delete-vegetable/<int:pk>/', views.delete_vegetable, name='delete_vegetable'),
    
    # Supplier URLs
    path('marketplace/', views.public_marketplace, name='public_marketplace'),
    path('marketplace/product/<int:pk>/', views.product_detail, name='product_detail'),
    path('marketplace/order/<int:pk>/', views.place_order, name='place_order'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('supplier/marketplace/', views.supplier_marketplace, name='supplier_marketplace'),
    path('supplier/purchase/<int:pk>/', views.purchase_from_farmer, name='purchase_from_farmer'),
    
    # Customer URLs
    path('customer/marketplace/', views.customer_marketplace, name='customer_marketplace'),
    path('customer/order/<int:pk>/', views.order_from_supplier, name='order_from_supplier'),
    path('customer/profile/', views.customer_profile, name='customer_profile'),
    
    # Weather URL
    path('weather/', views.weather_view, name='weather'),
    path('reports/', views.reports_view, name='reports'),
]