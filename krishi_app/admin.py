from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Vegetable, SupplierPurchase, SupplierInventory, CustomerOrder, Feedback

# Inline for UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__role')
    
    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except UserProfile.DoesNotExist:
            return 'No Profile'
    get_role.short_description = 'Role'

# UserProfile admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'has_image']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['user']
    
    def has_image(self, obj):
        return bool(obj.profile_image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

# Re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Vegetable)
class VegetableAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'quantity', 'unit', 'price_per_unit', 'available', 'created_at']
    list_filter = ['available', 'unit', 'created_at']
    search_fields = ['name', 'farmer__username']

@admin.register(SupplierPurchase)
class SupplierPurchaseAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'vegetable', 'quantity', 'total_price', 'status', 'purchased_at']
    list_filter = ['status', 'purchased_at']
    search_fields = ['supplier__username', 'vegetable__name']

@admin.register(SupplierInventory)
class SupplierInventoryAdmin(admin.ModelAdmin):
    list_display = ['vegetable_name', 'supplier', 'quantity', 'unit', 'price_per_unit', 'available']
    list_filter = ['available', 'unit']
    search_fields = ['vegetable_name', 'supplier__username']

@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'supplier_inventory', 'quantity', 'total_price', 'status', 'ordered_at']
    list_filter = ['status', 'ordered_at']
    search_fields = ['customer__username', 'supplier_inventory__vegetable_name']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['full_name', 'email', 'message']
    readonly_fields = ['created_at']

# Customize admin site
admin.site.site_header = 'Krishi Admin Panel'
admin.site.site_title = 'Krishi Admin'
admin.site.index_title = 'Welcome to Krishi Administration'
