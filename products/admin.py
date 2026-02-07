from django.contrib import admin
from .models import Product, Collection

# Register your models here.
@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'featured_product']  
    search_fields = ['name']        


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'inventory']  
    search_fields = ['name']
    list_filter = ['collection']
    prepopulated_fields = {'slug': ('name',)}
    def inventory_status(self, obj):
        if obj.inventory < 10:
            return 'Low'
        return 'OK'