from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.safestring import mark_safe
from django import forms
from .models import UserProfile, Vegetable, CustomerOrder, Feedback

# Custom form for UserProfile inline
class UserProfileInlineForm(forms.ModelForm):
    APPROVAL_CHOICES = [
        (True, '✓ Approved'),
        (False, '⏳ Pending'),
    ]
    
    approval_status = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.RadioSelect,
        required=False,
        label='Approval Status (Farmers Only)'
    )
    
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Only show approval status for farmers
            if self.instance.role == 'farmer':
                self.fields['approval_status'].initial = self.instance.is_approved
            else:
                # Hide the field for non-farmers
                self.fields['approval_status'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'approval_status' in self.cleaned_data and instance.role == 'farmer':
            new_status = self.cleaned_data['approval_status'] == 'True'
            if instance.is_approved != new_status:
                instance.is_approved = new_status
                if new_status:
                    instance.approval_date = timezone.now()
                else:
                    instance.approval_date = None
        if commit:
            instance.save()
        return instance

# Inline for UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ('approval_date',)
    fields = ('role', 'phone_number', 'address', 'address2', 'address3', 'temporary_address', 'temp_phone', 'profile_image', 'approval_status')
    form = UserProfileInlineForm

# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role', 'get_approval_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__role', 'userprofile__is_approved')
    actions = ['approve_farmers', 'reject_farmers']
    
    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except UserProfile.DoesNotExist:
            # Check if user is admin/superuser
            if obj.is_superuser:
                return 'Admin'
            return 'No Profile'
    get_role.short_description = 'Role'
    
    def get_approval_status(self, obj):
        try:
            profile = obj.userprofile
            if profile.role == 'farmer':
                return 'Approved' if profile.is_approved else 'Pending'
            return 'N/A'
        except UserProfile.DoesNotExist:
            # Admin users don't need approval
            if obj.is_superuser:
                return 'N/A'
            return 'No Profile'
    get_approval_status.short_description = 'Approval Status'
    
    def approve_farmers(self, request, queryset):
        # Only approve farmers that are not already approved
        farmers_to_approve = []
        for user in queryset:
            try:
                profile = user.userprofile
                if profile.role == 'farmer' and not profile.is_approved:
                    profile.is_approved = True
                    profile.approval_date = timezone.now()
                    profile.save()
                    farmers_to_approve.append(user)
            except UserProfile.DoesNotExist:
                continue
        self.message_user(request, f'{len(farmers_to_approve)} farmer(s) have been approved.')
    approve_farmers.short_description = 'Approve selected farmers'
    
    def reject_farmers(self, request, queryset):
        # Reject (unapprove) farmers
        farmers_to_reject = []
        for user in queryset:
            try:
                profile = user.userprofile
                if profile.role == 'farmer' and profile.is_approved:
                    profile.is_approved = False
                    profile.approval_date = None
                    profile.save()
                    farmers_to_reject.append(user)
            except UserProfile.DoesNotExist:
                continue
        self.message_user(request, f'{len(farmers_to_reject)} farmer(s) have been rejected.')
    reject_farmers.short_description = 'Reject selected farmers'

# UserProfile admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'has_image', 'approval_status']
    list_filter = ['role', 'is_approved']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['user', 'approval_date']
    fields = ('user', 'role', 'phone_number', 'address', 'address2', 'address3', 'temporary_address', 'temp_phone', 'profile_image', 'approval_status')
    form = UserProfileInlineForm
    
    def has_image(self, obj):
        return bool(obj.profile_image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'
    
    def approval_status(self, obj):
        if obj.role == 'farmer':
            if obj.is_approved:
                return '✓ Approved'
            else:
                return '⏳ Pending'
        return '✓ N/A'
    approval_status.short_description = 'Approval Status'
    
    def approve_farmers(self, request, queryset):
        # Only approve farmers that are not already approved
        farmers_to_approve = queryset.filter(role='farmer', is_approved=False)
        updated = farmers_to_approve.update(is_approved=True, approval_date=timezone.now())
        self.message_user(request, f'{updated} farmer(s) have been approved.')
    approve_farmers.short_description = 'Approve selected farmers'
    
    def reject_farmers(self, request, queryset):
        # Reject (unapprove) farmers
        farmers_to_reject = queryset.filter(role='farmer', is_approved=True)
        updated = farmers_to_reject.update(is_approved=False, approval_date=None)
        self.message_user(request, f'{updated} farmer(s) have been rejected.')
    reject_farmers.short_description = 'Reject selected farmers'

# Re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Vegetable)
class VegetableAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'quantity', 'unit', 'price_per_unit', 'available', 'created_at']
    list_filter = ['available', 'unit', 'created_at']
    search_fields = ['name', 'farmer__username']

@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'vegetable', 'quantity', 'total_price', 'status', 'ordered_at']
    list_filter = ['status', 'ordered_at']
    search_fields = ['customer__username', 'vegetable__name']

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

# Custom dashboard view
from django.contrib.admin.sites import AdminSite
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count, Q

@staff_member_required
def custom_admin_index(request):
    """Custom admin dashboard with statistics"""
    # Get statistics
    user_count = User.objects.count()
    farmer_count = UserProfile.objects.filter(role='farmer').count()
    order_count = CustomerOrder.objects.count()
    vegetable_count = Vegetable.objects.count()

    # Recent orders
    recent_orders = CustomerOrder.objects.select_related('customer', 'vegetable').order_by('-ordered_at')[:10]

    # Financial statistics
    total_revenue = CustomerOrder.objects.filter(
        status__in=['confirmed', 'delivered']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    pending_orders = CustomerOrder.objects.filter(status='pending').count()
    confirmed_orders = CustomerOrder.objects.filter(status='confirmed').count()

    context = {
        'user_count': user_count,
        'farmer_count': farmer_count,
        'order_count': order_count,
        'vegetable_count': vegetable_count,
        'recent_orders': recent_orders,
        'total_revenue': f"{total_revenue:,.0f}",
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'avg_order_time': "2-3 days",  # You can calculate this based on your data
    }

    return render(request, 'admin/index.html', context)

# Override the default admin index
admin.site.index = custom_admin_index
