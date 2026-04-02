from django.contrib import admin
from .models import Category, Product, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'category', 'price_per_unit', 'unit', 'stock_quantity', 'min_order_qty', 'is_active', 'harvest_date']
    list_filter = ['category', 'harvest_date', 'is_active']
    search_fields = ['name', 'farmer__username']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Product Info', {'fields': ('farmer', 'category', 'name', 'image', 'description')}),
        ('Pricing & Stock', {'fields': ('price_per_unit', 'unit', 'stock_quantity', 'min_order_qty')}),
        ('Harvest', {'fields': ('harvest_date',)}),
        ('Status', {'fields': ('is_active', 'created_at')}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'quantity', 'total_price', 'status', 'delivery_mode', 'ordered_at']
    list_filter = ['status', 'delivery_mode', 'ordered_at']
    search_fields = ['customer__username', 'product__name', 'phone_number']
    list_editable = ['status']
    readonly_fields = ['ordered_at', 'accepted_at', 'shipped_at', 'delivered_at', 'total_price']
    fieldsets = (
        ('Order Info', {'fields': ('customer', 'product', 'quantity', 'total_price', 'status')}),
        ('Delivery', {'fields': ('delivery_address', 'phone_number', 'delivery_mode')}),
        ('Timeline', {'fields': ('ordered_at', 'accepted_at', 'shipped_at', 'delivered_at')}),
        ('Farmer Notes', {'fields': ('farmer_notes',)}),
    )
