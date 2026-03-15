from django.contrib import admin
from .models import Category, Product, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'category', 'price_per_kg', 'stock_quantity', 'harvest_date']
    list_filter = ['category', 'harvest_date']
    search_fields = ['name', 'farmer__username']
    readonly_fields = ['created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'quantity', 'total_price', 'status', 'ordered_at']
    list_filter = ['status']
    search_fields = ['customer__username', 'product__name']
    list_editable = ['status']
