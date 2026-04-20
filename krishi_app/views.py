from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.safestring import mark_safe
from decimal import Decimal
import re
import requests
import uuid
import hmac
import hashlib
import base64
import json
from django.conf import settings
from .models import UserProfile, Vegetable, CustomerOrder, Cart, CartItem, Feedback
from django.db.models import Sum, Avg
from django.db import models

def home(request):
    featured_products = Vegetable.objects.filter(available=True).order_by('-created_at')[:8]
    return render(request, 'home.html', {'featured_products': featured_products})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                # Check if user is a farmer and if they are approved
                try:
                    user_profile = user.userprofile
                    if user_profile.role == 'farmer' and not user_profile.is_approved:
                        messages.error(request, 'Your farmer account is pending admin approval. Please wait for approval to login.')
                        return render(request, 'registration/login.html')
                except UserProfile.DoesNotExist:
                    messages.error(request, 'User profile not found. Please contact support.')
                    return render(request, 'registration/login.html')
                
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
        except User.DoesNotExist:
            messages.error(request, 'Email not found. Please register first.')
    
    return render(request, 'registration/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'farmer')
        profile_image = request.FILES.get('profile_image')
        official_document = request.FILES.get('official_document')
        
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif len(username) > 30:
            errors.append('Username must be less than 30 characters.')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists. Please choose a different one.')
        
        if not email:
            errors.append('Email is required.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append('Please enter a valid email address.')
            if User.objects.filter(email=email).exists():
                errors.append('Email already exists. Please use a different email or login.')
        
        if not password1:
            errors.append('Password is required.')
        elif len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        elif len(password1) > 128:
            errors.append('Password is too long.')
        elif not re.search(r'[A-Za-z]', password1):
            errors.append('Password must contain at least one letter.')
        elif not re.search(r'[0-9]', password1):
            errors.append('Password must contain at least one number.')
        elif password1 != password2:
            errors.append('Passwords do not match.')
        
        if not first_name:
            errors.append('First name is required.')
        elif len(first_name) < 2:
            errors.append('First name must be at least 2 characters long.')
        elif len(first_name) > 30:
            errors.append('First name must be less than 30 characters.')
        elif not re.match(r'^[a-zA-Z\s]+$', first_name):
            errors.append('First name can only contain letters and spaces.')
        
        if not last_name:
            errors.append('Last name is required.')
        elif len(last_name) < 2:
            errors.append('Last name must be at least 2 characters long.')
        elif len(last_name) > 30:
            errors.append('Last name must be less than 30 characters.')
        elif not re.match(r'^[a-zA-Z\s]+$', last_name):
            errors.append('Last name can only contain letters and spaces.')
        
        if role not in ['farmer', 'expert', 'customer']:
            errors.append('Invalid role selected.')

        if role == 'farmer' and not official_document:
            errors.append('Official document is required for farmer registration.')
        
        if profile_image:
            if profile_image.size > 5 * 1024 * 1024:
                errors.append('Profile image size must be less than 5MB.')
            
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if profile_image.content_type not in allowed_types:
                errors.append('Profile image must be a JPEG, PNG, or GIF file.')

        if official_document:
            if official_document.size > 5 * 1024 * 1024:
                errors.append('Official document size must be less than 5MB.')

            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if official_document.content_type not in allowed_types:
                errors.append('Official document must be a JPEG, PNG, or GIF file.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
            }
            return render(request, 'registration/register.html', context)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        is_approved = True if role != 'farmer' else False

        UserProfile.objects.create(
            user=user,
            role=role,
            profile_image=profile_image,
            official_document=official_document,
            is_approved=is_approved
        )

        if role == 'farmer':
            messages.success(request, 'Registration successful! Your account is pending admin approval. You will receive an email once approved.')
        else:
            messages.success(request, 'Registration successful! Please login to continue.')
        return redirect('login')
    
    return render(request, 'registration/register.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logged out successfully')
        return redirect('home')
    return redirect('home')

@login_required
def get_new_orders_count(request):
    """API endpoint to get count of new (unviewed) orders for farmer - for real-time badge updates"""
    if request.user.userprofile.role != 'farmer':
        return JsonResponse({'count': 0, 'error': 'Only farmers can access this'})
    
    # Count unviewed orders that are pending or confirmed
    count = CustomerOrder.objects.filter(
        vegetable__farmer=request.user, 
        status__in=['pending', 'confirmed'],
        viewed_by_farmer=False
    ).count()
    return JsonResponse({'count': count})

@login_required
def dashboard(request):
    user_profile = request.user.userprofile
    if user_profile.role == 'customer':
        return redirect('customer_dashboard')
    elif user_profile.role == 'farmer':
        vegetables = Vegetable.objects.filter(farmer=request.user)
        total_vegetables = vegetables.count()
        available_vegetables = vegetables.filter(available=True).count()
        sold_out = vegetables.filter(available=False).count()
        
        # Calculate earnings from direct customer orders
        total_earnings = CustomerOrder.objects.filter(vegetable__farmer=request.user).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Calculate total orders
        total_orders = CustomerOrder.objects.filter(vegetable__farmer=request.user).count()
        
        # Get recent orders
        recent_orders = CustomerOrder.objects.filter(vegetable__farmer=request.user).order_by('-ordered_at')[:5]
        
        context = {
            'user_role': user_profile.role,
            'user_profile': user_profile,
            'vegetables': vegetables,
            'total_vegetables': total_vegetables,
            'available_vegetables': available_vegetables,
            'sold_out': sold_out,
            'total_earnings': total_earnings,
            'total_orders': total_orders,
            'recent_orders': recent_orders,
            'new_orders_count': CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['pending', 'confirmed'], viewed_by_farmer=False).count(),
        }
        return render(request, 'dashboard/farmer_dashboard.html', context)
    elif user_profile.role == 'expert':
        return render(request, 'dashboard/expert_dashboard.html', {'user_role': user_profile.role})
    return redirect('home')

@login_required
def customer_dashboard(request):
    """Customer dashboard view at /customer/dashboard/"""
    user_profile = request.user.userprofile
    orders = CustomerOrder.objects.filter(customer=request.user)
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    in_transit = orders.filter(status='confirmed').count()
    recommended = Vegetable.objects.filter(available=True).order_by('-created_at')[:3]
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    context = {
        'user_role': user_profile.role,
        'user_profile': user_profile,
        'orders': orders,
        'total_spent': total_spent,
        'in_transit': in_transit,
        'recommended': recommended,
        'cart': cart,
    }
    return render(request, 'dashboard/customer_dashboard.html', context)

def about(request):
    return render(request, 'about.html')

def blog(request):
    return render(request, 'blog.html')

def blog_organic_future(request):
    return render(request, 'blog/organic_future.html')

def blog_smart_irrigation(request):
    return render(request, 'blog/smart_irrigation.html')

def blog_climate_change(request):
    return render(request, 'blog/climate_change.html')

def blog_direct_market(request):
    return render(request, 'blog/direct_market.html')

def blog_soil_testing(request):
    return render(request, 'blog/soil_testing.html')

def blog_pest_management(request):
    return render(request, 'blog/pest_management.html')

def blog_crop_rotation(request):
    return render(request, 'blog/crop_rotation.html')

def organic_crops(request):
    return render(request, 'organic_crops.html')

def solutions(request):
    return render(request, 'solutions.html')

def smart_farming(request):
    return render(request, 'solutions/smart_farming.html')

def market_intelligence(request):
    return render(request, 'solutions/market_intelligence.html')

def supply_chain(request):
    return render(request, 'solutions/supply_chain.html')

def expert_advisory(request):
    return render(request, 'solutions/expert_advisory.html')


@login_required
def customer_profile(request):
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')
    profile = request.user.userprofile
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_info':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            profile.phone_number = request.POST.get('phone_number', '').strip()
            profile.address = request.POST.get('address', '').strip()
            profile.address2 = request.POST.get('address2', '').strip()
            profile.address3 = request.POST.get('address3', '').strip()
            request.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully.')
        elif action == 'clear_address':
            address_field = request.POST.get('address_field')
            if address_field == 'address':
                # Clear default address
                profile.address = ''
                profile.save()
                messages.success(request, 'Default Address cleared successfully.')
            elif address_field == 'address2':
                # Clear address2 and shift address3 to address2
                profile.address2 = profile.address3
                profile.address3 = ''
                profile.save()
                messages.success(request, 'Address 1 cleared successfully.')
            elif address_field == 'address3':
                # Clear address3
                profile.address3 = ''
                profile.save()
                messages.success(request, 'Address 2 cleared successfully.')
            else:
                messages.error(request, 'Invalid address field.')
        elif action == 'change_password':
            current = request.POST.get('current_password')
            new_pass = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif len(new_pass) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            elif new_pass != confirm:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_pass)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
        return redirect('customer_profile')
    return render(request, 'dashboard/customer_profile.html', {'profile': profile})


@login_required
def farmer_profile(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    profile = request.user.userprofile
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_info':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            profile.phone_number = request.POST.get('phone_number', '').strip()
            profile.address = request.POST.get('address', '').strip()
            request.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully.')
        elif action == 'change_password':
            current = request.POST.get('current_password')
            new_pass = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif len(new_pass) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            elif new_pass != confirm:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_pass)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
        return redirect('farmer_profile')
    return render(request, 'dashboard/farmer_profile.html', {'profile': profile, 'new_orders_count': CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['pending', 'confirmed'], viewed_by_farmer=False).count()})


# Farmer Views
@login_required
def farmer_stock(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    vegetables = Vegetable.objects.filter(farmer=request.user).order_by('-created_at')
    total_quantity = vegetables.aggregate(total=Sum('quantity'))['total'] or 0
    avg_price = vegetables.aggregate(avg=models.Avg('price_per_unit'))['avg'] or 0
    return render(request, 'dashboard/farmer_stock.html', {
        'vegetables': vegetables,
        'total_quantity': total_quantity,
        'avg_price': avg_price,
        'new_orders_count': CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['pending', 'confirmed'], viewed_by_farmer=False).count(),
    })

@login_required
def farmer_products(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    vegetables = Vegetable.objects.filter(farmer=request.user).order_by('-created_at')
    paginator = Paginator(vegetables, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/farmer_products.html', {'vegetables': page_obj, 'paginator': paginator, 'new_orders_count': CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['pending', 'confirmed'], viewed_by_farmer=False).count()})

@login_required
def add_vegetable(request):
    if request.user.userprofile.role != 'farmer':
        messages.error(request, 'Only farmers can add vegetables')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Create Vegetable (old system for backward compatibility)
        veg = Vegetable.objects.create(
            farmer=request.user,
            name=request.POST['name'],
            category=request.POST.get('category', 'vegetable'),
            quantity=request.POST.get('stock') or request.POST.get('quantity'),
            unit=request.POST['unit'],
            min_order_qty=request.POST.get('min_order_qty') or 1,
            base_price=request.POST.get('base_price') or request.POST['price_per_unit'],
            price_per_unit=request.POST['price_per_unit'],
            discount_price=request.POST.get('discount_price') or None,
            harvest_date=request.POST.get('harvest_date') or None,
            shelf_life_days=request.POST.get('shelf_life_days') or 7,
            is_farmers_special=request.POST.get('is_farmers_special') == 'on',
            description=request.POST.get('description', ''),
            image=request.FILES.get('image')
        )
        
        # Also create Product (for bulk cart system)
        from products.models import Product, Category as ProductCategory
        
        # Get or create category
        cat_map = {'vegetable': 'Vegetable', 'fruit': 'Fruit', 'grain': 'Grain', 'spice': 'Spice', 'other': 'Other'}
        cat_name = cat_map.get(request.POST.get('category', 'vegetable'), 'Vegetable')
        category, _ = ProductCategory.objects.get_or_create(name=cat_name)
        
        Product.objects.create(
            farmer=request.user,
            category=category,
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            price_per_unit=float(request.POST['price_per_unit']),
            unit=request.POST['unit'],
            stock_quantity=float(request.POST.get('stock') or request.POST.get('quantity')),
            min_order_qty=float(request.POST.get('min_order_qty') or 1),
            harvest_date=request.POST.get('harvest_date') or None,
            image=request.FILES.get('image'),
            is_active=True
        )
        
        messages.success(request, 'Product added successfully')
        return redirect('farmer_products')
    return render(request, 'dashboard/add_vegetable.html')

@login_required
def edit_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    if request.method == 'POST':
        vegetable.name = request.POST['name']
        vegetable.category = request.POST.get('category', vegetable.category)
        vegetable.quantity = request.POST['quantity']
        vegetable.unit = request.POST['unit']
        vegetable.min_order_qty = request.POST.get('min_order_qty') or vegetable.min_order_qty
        vegetable.base_price = request.POST.get('base_price') or vegetable.base_price
        vegetable.price_per_unit = request.POST['price_per_unit']
        vegetable.discount_price = request.POST.get('discount_price') or None
        vegetable.harvest_date = request.POST.get('harvest_date') or None
        vegetable.shelf_life_days = request.POST.get('shelf_life_days') or 7
        vegetable.is_farmers_special = request.POST.get('is_farmers_special') == 'on'
        vegetable.description = request.POST.get('description', '')
        if request.FILES.get('image'):
            vegetable.image = request.FILES['image']
        vegetable.available = request.POST.get('available') == 'on'
        vegetable.save()
        
        # Sync to Product model (bulk cart system)
        from products.models import Product, Category as ProductCategory
        
        cat_map = {'vegetable': 'Vegetable', 'fruit': 'Fruit', 'grain': 'Grain', 'spice': 'Spice', 'other': 'Other'}
        cat_name = cat_map.get(request.POST.get('category', 'vegetable'), 'Vegetable')
        category, _ = ProductCategory.objects.get_or_create(name=cat_name)
        
        # Update or create Product with same name
        product, created = Product.objects.update_or_create(
            farmer=request.user,
            name=vegetable.name,
            defaults={
                'category': category,
                'description': vegetable.description,
                'price_per_unit': float(vegetable.price_per_unit),
                'unit': vegetable.unit,
                'stock_quantity': float(vegetable.quantity),
                'min_order_qty': float(vegetable.min_order_qty),
                'harvest_date': vegetable.harvest_date,
                'image': vegetable.image,
                'is_active': vegetable.available
            }
        )
        
        messages.success(request, 'Product updated successfully')
        return redirect('farmer_products')
    return render(request, 'dashboard/edit_vegetable.html', {'vegetable': vegetable})

@login_required
def view_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    return render(request, 'dashboard/view_vegetable.html', {'vegetable': vegetable})

@login_required
@login_required
def delete_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    
    # Also delete synced Product (bulk cart system)
    from products.models import Product
    Product.objects.filter(
        farmer=request.user,
        name=vegetable.name
    ).delete()
    
    vegetable.delete()
    messages.success(request, 'Vegetable deleted successfully')
    return redirect('farmer_products')

def public_marketplace(request):
    q = request.GET.get('q', '')
    category = request.GET.get('category', 'all')
    
    vegetables = Vegetable.objects.filter(available=True).select_related('farmer')
    
    # Auto-mark as sold out if quantity is 0
    for v in vegetables:
        if v.quantity <= 0:
            v.available = False
            v.save()
    
    vegetables = Vegetable.objects.filter(available=True).select_related('farmer')
    
    if category and category != 'all':
        vegetables = vegetables.filter(category=category)
    
    return render(request, 'marketplace.html', {
        'vegetables': vegetables,
        'search_query': q,
        'categories': Vegetable.CATEGORY_CHOICES,
        'selected_category': category
    })

def product_detail(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk)
    # Check if user is authenticated and is a customer
    is_customer = request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'customer'
    
    # If public user (not authenticated), show public product detail template
    if not request.user.is_authenticated:
        return render(request, 'public_product_detail.html', {'vegetable': vegetable})
    
    # If authenticated customer, show customer marketplace product detail
    if is_customer:
        return render(request, 'product_detail.html', {'vegetable': vegetable})
    
    # If authenticated but not a customer (farmer/supplier), redirect to home
    messages.error(request, 'Only customers can view this page')
    return redirect('home')

@login_required
def place_order(request, pk):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can place orders')
        return redirect('login')

    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)

    if request.method == 'POST':
        quantity = float(request.POST.get('quantity', 0))

        if quantity <= 0:
            messages.error(request, 'Enter a valid quantity')
            return redirect('product_detail', pk=pk)

        if quantity > float(vegetable.quantity):
            messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} available')
            return redirect('product_detail', pk=pk)

        total_price = quantity * float(vegetable.price_per_unit)
        CustomerOrder.objects.create(
            customer=request.user,
            vegetable=vegetable,
            quantity=quantity,
            total_price=total_price
        )

        vegetable.quantity -= quantity
        if vegetable.quantity <= 0:
            vegetable.available = False
        vegetable.save()

        messages.success(request, f'Order placed for {quantity} {vegetable.unit} of {vegetable.name}!')
        return redirect('customer_marketplace')

    return redirect('product_detail', pk=pk)

@login_required
def add_to_cart(request, pk):
    # Check if user is authenticated first
    if not request.user.is_authenticated:
        messages.error(request, '🔐 Please login first to add items to cart')
        return redirect('login')
    
    # Check if user is a customer
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can add to cart')
        return redirect('login')

    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)

    if request.method == 'POST':
        try:
            quantity_str = request.POST.get('quantity', '1').strip()
            if not quantity_str:
                quantity_str = '1'
            quantity = Decimal(quantity_str)
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity')
            return redirect('customer_marketplace')
        
        # Edge case: Validate quantity is positive
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('customer_marketplace')
        
        # Edge case: Check stock availability for new quantity
        if quantity > vegetable.quantity:
            messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} available')
            return redirect('customer_marketplace')
        
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        
        try:
            item = CartItem.objects.get(cart=cart, vegetable=vegetable)
            new_total = item.quantity + Decimal('1')
            if new_total > vegetable.quantity:
                messages.warning(request, f'Cannot add more. Only {vegetable.quantity} {vegetable.unit} available. You already have {item.quantity} in cart.')
                return redirect('customer_marketplace')
            item.quantity = new_total
            item.save()
            messages.success(request, f'✓ {vegetable.name} quantity updated to {item.quantity} {vegetable.unit}')
        except CartItem.DoesNotExist:
            min_qty = vegetable.min_order_qty
            if min_qty > vegetable.quantity:
                messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} available')
                return redirect('customer_marketplace')
            item = CartItem.objects.create(cart=cart, vegetable=vegetable, quantity=min_qty)
            messages.success(request, f'✓ {vegetable.name} added to cart! (Min order: {min_qty} {vegetable.unit})')
        
        return redirect('customer_marketplace')
    
    return redirect('customer_marketplace')

@login_required
def cart_view(request):
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    return render(request, 'dashboard/customer_cart.html', {'cart': cart})

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart')
    return redirect('cart')

@login_required
def increase_cart_quantity(request, pk):
    """Increase the quantity of a cart item."""
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    
    # Check if increasing quantity won't exceed available stock
    if item.quantity < item.vegetable.quantity:
        item.quantity += 1
        item.save()
        messages.success(request, f'Increased quantity of {item.vegetable.name}')
    else:
        messages.warning(request, f'Only {item.vegetable.quantity} {item.vegetable.unit} available')
    
    return redirect('cart')

@login_required
def update_cart_quantity(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    if request.method == 'POST':
        try:
            quantity = Decimal(request.POST.get('quantity', '1').strip())
        except Exception:
            messages.error(request, 'Invalid quantity')
            return redirect('cart')
        min_qty = item.vegetable.min_order_qty
        max_qty = item.vegetable.quantity
        if quantity < min_qty:
            messages.error(request, f'Minimum order quantity is {min_qty} {item.vegetable.unit}')
        elif quantity > max_qty:
            messages.error(request, f'Only {max_qty} {item.vegetable.unit} available')
        else:
            item.quantity = quantity
            item.save()
            messages.success(request, f'Quantity updated to {quantity} {item.vegetable.unit}')
    return redirect('cart')

@login_required
def decrease_cart_quantity(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    min_qty = item.vegetable.min_order_qty
    if item.quantity - 1 < min_qty:
        messages.error(request, f'Minimum order quantity for {item.vegetable.name} is {min_qty} {item.vegetable.unit}. Cannot go below that.')
    else:
        item.quantity -= 1
        item.save()
    return redirect('cart')

@login_required
def buy_now_action(request, pk):
    """Add product to cart and redirect to checkout page (for 'Buy Now' button)."""
    # Check if user is authenticated first
    if not request.user.is_authenticated:
        messages.error(request, '🔐 Please login first to buy products')
        return redirect('login')
    
    # Check if user is a customer
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can buy products')
        return redirect('login')

    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)

    if request.method == 'POST':
        try:
            quantity = Decimal(request.POST.get('quantity', str(vegetable.min_order_qty)).strip())
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity')
            return redirect('customer_marketplace')
        
        # Ensure quantity is at least min_order_qty
        if quantity < vegetable.min_order_qty:
            quantity = vegetable.min_order_qty
        
        # Edge case: Check stock availability
        if quantity > vegetable.quantity:
            messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} of {vegetable.name} available')
            return redirect('customer_marketplace')
        
        # Add to cart (duplicate products will increase quantity automatically)
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        try:
            item = CartItem.objects.get(cart=cart, vegetable=vegetable)
            # Check if adding more quantity would exceed stock
            if item.quantity + quantity > vegetable.quantity:
                messages.warning(request, f'You already have {item.quantity} {vegetable.unit} of this. Only {vegetable.quantity} available total.')
                checkout_url = reverse('checkout_page')
                return redirect(f'{checkout_url}?items={item.pk}')
            item.quantity += quantity
        except CartItem.DoesNotExist:
            item = CartItem(cart=cart, vegetable=vegetable, quantity=quantity)
        # Ensure quantity is at least min_order_qty
        if item.quantity < vegetable.min_order_qty:
            item.quantity = vegetable.min_order_qty
        
        item.save()
        messages.success(request, f'{quantity} {vegetable.unit} of {vegetable.name} added!')
        # Redirect to checkout page with only this item
        checkout_url = reverse('checkout_page')
        return redirect(f'{checkout_url}?items={item.pk}')
    
    return redirect('customer_marketplace')

@login_required
def buy_selected_items(request):
    """Process payment for selected cart items"""
    if request.method in ['POST', 'GET']:
        if request.user.userprofile.role != 'customer':
            return redirect('dashboard')
        
        # Get selected item IDs
        selected_items_str = request.POST.get('selected_items') or request.GET.get('selected_items', '')
        
        # Handle case where eSewa appends ?data= blindly to the URL causing "28?data=..."
        if selected_items_str and '?' in selected_items_str:
            selected_items_str = selected_items_str.split('?')[0]
            
        if not selected_items_str:
            messages.error(request, 'No items selected')
            return redirect('cart')
        
        try:
            selected_item_ids = list(map(int, selected_items_str.split(',')))
        except (ValueError, AttributeError):
            messages.error(request, 'Invalid item selection')
            return redirect('cart')
        
        # Get cart and validate items
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        selected_items = cart.items.filter(id__in=selected_item_ids).select_related('vegetable')
        
        if not selected_items:
            messages.error(request, 'Selected items not found in cart')
            return redirect('cart')
        
        # Validate stock for selected items
        for item in selected_items:
            if item.quantity > item.vegetable.quantity:
                messages.error(request, f'Only {item.vegetable.quantity} {item.vegetable.unit} of {item.vegetable.name} available')
                return redirect('cart')
            if item.quantity < item.vegetable.min_order_qty:
                messages.error(request, f'Minimum order quantity for {item.vegetable.name} is {item.vegetable.min_order_qty} {item.vegetable.unit}.')
                return redirect('cart')
        
        # Check if this is an eSewa success callback (Safely checking the raw query string because of duplicate ? signs)
        is_paid = 'data=' in request.META.get('QUERY_STRING', '')
        order_status = 'confirmed' if is_paid else 'pending'

        # Create orders for selected items
        try:
            for item in selected_items:
                # Get selected address for this order
                selected_address = request.POST.get('selected_address', 'address')
                
                # Determine shipping address and phone based on selection
                user_profile = request.user.userprofile
                if selected_address == 'address':
                    shipping_addr = user_profile.temporary_address or user_profile.address
                    shipping_phone = user_profile.temp_phone or user_profile.phone_number
                elif selected_address == 'address2':
                    shipping_addr = user_profile.temporary_address or user_profile.address2
                    shipping_phone = user_profile.temp_phone or user_profile.phone_number
                elif selected_address == 'address3':
                    shipping_addr = user_profile.temporary_address or user_profile.address3
                    shipping_phone = user_profile.temp_phone or user_profile.phone_number
                else:
                    # Fallback to primary address
                    shipping_addr = user_profile.temporary_address or user_profile.address
                    shipping_phone = user_profile.temp_phone or user_profile.phone_number
                
                shipping_address_full = f"{shipping_addr}\nPhone: {shipping_phone}"
                
                CustomerOrder.objects.create(
                    customer=request.user,
                    vegetable=item.vegetable,
                    quantity=item.quantity,
                    total_price=item.quantity * item.vegetable.price_per_unit,
                    status=order_status,
                    shipping_address=shipping_address_full
                )
                # Update vegetable stock
                item.vegetable.quantity -= item.quantity
                if item.vegetable.quantity <= 0:
                    item.vegetable.available = False
                item.vegetable.save()
            
            # Remove only selected items from cart
            selected_items.delete()
            messages.success(request, 'Order placed successfully!')
            return redirect('customer_orders')
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('cart')
    
    return redirect('cart')

@login_required
def checkout_cart(request):
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    items = cart.items.select_related('vegetable').all()
    if not items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    for item in items:
        if item.quantity > item.vegetable.quantity:
            messages.error(request, f'Only {item.vegetable.quantity} {item.vegetable.unit} of {item.vegetable.name} available')
            return redirect('cart')
        if item.quantity < item.vegetable.min_order_qty:
            messages.error(request, f'Minimum order quantity for {item.vegetable.name} is {item.vegetable.min_order_qty} {item.vegetable.unit}.')
            return redirect('cart')
    # Safely checking the raw query string for eSewa's data payload
    is_paid = 'data=' in request.META.get('QUERY_STRING', '')
    order_status = 'confirmed' if is_paid else 'pending'
    
    for item in items:
        # Get selected address for this order
        selected_address = request.POST.get('selected_address', 'address')
        
        # Determine shipping address and phone based on selection
        user_profile = request.user.userprofile
        if selected_address == 'address':
            shipping_addr = user_profile.temporary_address or user_profile.address
            shipping_phone = user_profile.temp_phone or user_profile.phone_number
        elif selected_address == 'address2':
            shipping_addr = user_profile.temporary_address or user_profile.address2
            shipping_phone = user_profile.temp_phone or user_profile.phone_number
        elif selected_address == 'address3':
            shipping_addr = user_profile.temporary_address or user_profile.address3
            shipping_phone = user_profile.temp_phone or user_profile.phone_number
        else:
            # Fallback to primary address
            shipping_addr = user_profile.temporary_address or user_profile.address
            shipping_phone = user_profile.temp_phone or user_profile.phone_number
        
        shipping_address_full = f"{shipping_addr}\nPhone: {shipping_phone}"
        
        CustomerOrder.objects.create(
            customer=request.user,
            vegetable=item.vegetable,
            quantity=item.quantity,
            total_price=item.quantity * item.vegetable.price_per_unit,
            status=order_status,
            shipping_address=shipping_address_full
        )
        item.vegetable.quantity -= item.quantity
        if item.vegetable.quantity <= 0:
            item.vegetable.available = False
        item.vegetable.save()
    cart.items.all().delete()
    messages.success(request, 'All orders placed successfully!')
    return redirect('dashboard')

# Customer Views
@login_required
def customer_marketplace(request):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can access this page')
        return redirect('dashboard')
    
    q = request.GET.get('q', '')
    
    # Get all available products from Vegetable (direct from Farmers)
    vegetables = list(Vegetable.objects.all())
    
    # Auto-mark as sold out if quantity is 0
    for v in vegetables:
        if v.quantity <= 0 and v.available:
            v.available = False
            v.save()
    
    # Filter by search query
    if q:
        vegetables = [v for v in vegetables if q.lower() in v.name.lower()]
    
    # Add necessary attributes for template compatibility
    for v in vegetables:
        v.source = 'vegetable'
        v.vegetable_name = v.name
        v.supplier_first_name = v.farmer.first_name
        v.supplier_last_name = v.farmer.last_name
        v.supplier_id = v.farmer.id
        # Ensure available is False if quantity is 0
        if v.quantity <= 0:
            v.available = False
    
    combined_products = vegetables
    
    # Create a custom paginator for combined results
    paginator = Paginator(combined_products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get cart for floating icon
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    return render(request, 'dashboard/dashboard_marketplace.html', {'page_obj': page_obj, 'search_query': q, 'paginator': paginator, 'cart': cart})

@login_required
def customer_orders(request):
    """Display all orders placed by the customer."""
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can view orders')
        return redirect('dashboard')
    
    # Get all orders for the customer
    orders = CustomerOrder.objects.filter(customer=request.user).select_related('vegetable').order_by('-ordered_at')
    
    from django.utils import timezone
    from datetime import timedelta

    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
        
    # Filter by date if provided
    date_filter = request.GET.get('date', 'all')
    now = timezone.now()
    if date_filter == 'today':
        orders = orders.filter(ordered_at__date=now.date())
    elif date_filter == '1_week':
        orders = orders.filter(ordered_at__gte=now - timedelta(days=7))
    elif date_filter == '3_weeks':
        orders = orders.filter(ordered_at__gte=now - timedelta(days=21))
    elif date_filter == '1_month':
        orders = orders.filter(ordered_at__gte=now - timedelta(days=30))
    elif date_filter == '3_months':
        orders = orders.filter(ordered_at__gte=now - timedelta(days=90))
    
    # Calculate statistics
    total_orders = CustomerOrder.objects.filter(customer=request.user).count()
    pending_orders = CustomerOrder.objects.filter(customer=request.user, status='pending').count()
    confirmed_orders = CustomerOrder.objects.filter(customer=request.user, status='confirmed').count()
    delivered_orders = CustomerOrder.objects.filter(customer=request.user, status='delivered').count()
    total_spent = CustomerOrder.objects.filter(customer=request.user).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Get cart for floating icon
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    # Build orders data for JavaScript
    orders_data = {}
    for o in orders_page:
        orders_data[str(o.id)] = {
            'id': str(o.id),
            'date': o.ordered_at.strftime('%b %d, %Y') if o.ordered_at else 'N/A',
            'total': str(o.total_price),
            'status': o.status,
            'productName': o.vegetable.name,
            'quantity': str(o.quantity),
            'unitPrice': str(o.vegetable.price_per_unit),
            'unit': o.vegetable.unit,
            'buyerName': f"{request.user.first_name} {request.user.last_name}",
            'buyerPhone': request.user.userprofile.phone_number or 'N/A',
            'buyerAddress': o.shipping_address or request.user.userprofile.address or 'Address not provided'
        }
    
    # Mark JSON as safe so Django won't escape it
    orders_json_safe = mark_safe(json.dumps(orders_data))
    
    # Add extra details for modal display in table
    for o in orders_page:
        o.product_name = o.vegetable.name
        o.unit_price = o.vegetable.price_per_unit
        o.unit = o.vegetable.unit
        o.buyer_address = o.shipping_address or o.customer.userprofile.address
    
    context = {
        'orders': orders_page,
        'orders_json': orders_json_safe,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'total_spent': total_spent,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'paginator': paginator,
        'cart': cart,
    }
    
    return render(request, 'dashboard/customer_orders.html', context)

@login_required
def download_order_receipt(request, pk):
    """Generate and download order receipt as PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    from django.http import HttpResponse
    
    # Get the order
    order = get_object_or_404(CustomerOrder, id=pk, customer=request.user)
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#22C55E'),
        spaceAfter=6,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F2937'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Title
    elements.append(Paragraph('KrishiConnect', title_style))
    elements.append(Paragraph('Order Receipt', styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Order details table
    order_data = [
        ['Order ID:', '#' + str(order.id), 'Date:', order.ordered_at.strftime('%b %d, %Y') if order.ordered_at else 'N/A'],
        ['Total Amount:', '₹' + str(order.total_price), 'Status:', order.status.title()],
    ]
    
    order_table = Table(order_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    order_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 11),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Customer details
    elements.append(Paragraph('Customer Details', heading_style))
    customer_name = f"{request.user.first_name} {request.user.last_name}".strip()
    customer_phone = request.user.userprofile.phone_number or 'N/A'
    customer_address = order.shipping_address or request.user.userprofile.address or 'Address not provided'
    
    customer_info = f"""
    <b>Name:</b> {customer_name}<br/>
    <b>Phone:</b> {customer_phone}<br/>
    <b>Address:</b> {customer_address}
    """
    elements.append(Paragraph(customer_info, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table
    elements.append(Paragraph('Items Purchased', heading_style))
    items_data = [
        ['Product', 'Quantity', 'Unit Price', 'Subtotal']
    ]
    items_data.append([
        order.vegetable.name,
        str(order.quantity) + ' ' + order.vegetable.unit,
        '₹' + str(order.vegetable.price_per_unit),
        '₹' + str(order.total_price)
    ])
    
    items_table = Table(items_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Total
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#15803D'),
        alignment=2  # Right
    )
    elements.append(Paragraph(f'<b>Total Amount: ₹{order.total_price}</b>', total_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1  # Center
    )
    elements.append(Paragraph('Thank you for shopping with KrishiConnect!', footer_style))
    elements.append(Paragraph('For support: support@krishisphere.com', footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Return PDF as download
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order-{order.id}-receipt.pdf"'
    return response

@login_required
def order_from_supplier(request, pk):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can order')
        return redirect('dashboard')
    
    vegetable = get_object_or_404(Vegetable, pk=pk)
    
    if request.method == 'POST':
        quantity = float(request.POST['quantity'])
        total_price = quantity * float(vegetable.price_per_unit)
        
        CustomerOrder.objects.create(
            customer=request.user,
            vegetable=vegetable,
            quantity=quantity,
            total_price=total_price
        )
        
        vegetable.quantity -= quantity
        if vegetable.quantity <= 0:
            vegetable.available = False
        vegetable.save()
        
        messages.success(request, 'Order placed successfully')
        return redirect('customer_marketplace')
    
    # Get cart for floating icon
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    return render(request, 'dashboard/order_vegetable_dashboard.html', {'inventory': inventory, 'cart': cart})

# Weather View
def reports_view(request):
    from django.db.models import Sum, Count
    total_farmers = UserProfile.objects.filter(role='farmer').count()
    total_customers = UserProfile.objects.filter(role='customer').count()
    total_products = Vegetable.objects.count()
    available_products = Vegetable.objects.filter(available=True).count()
    total_orders = CustomerOrder.objects.count()
    total_revenue = CustomerOrder.objects.aggregate(total=Sum('total_price'))['total'] or 0
    pending_orders = CustomerOrder.objects.filter(status='pending').count()
    confirmed_orders = CustomerOrder.objects.filter(status='confirmed').count()
    delivered_orders = CustomerOrder.objects.filter(status='delivered').count()
    top_products = CustomerOrder.objects.values('vegetable__name').annotate(
        vegetable_name=models.F('vegetable__name'),
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:6]
    max_qty = max((p['total_qty'] for p in top_products), default=1)
    category_stats = Vegetable.objects.values('category').annotate(count=Count('id')).order_by('-count')
    top_farmers = Vegetable.objects.values('farmer__username').annotate(product_count=Count('id')).order_by('-product_count')[:5]
    recent_orders = CustomerOrder.objects.select_related('customer', 'vegetable').order_by('-ordered_at')[:8]
    return render(request, 'reports.html', {
        'total_farmers': total_farmers,
        'total_customers': total_customers,
        'total_products': total_products,
        'available_products': available_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'top_products': top_products,
        'max_qty': max_qty,
        'category_stats': category_stats,
        'top_farmers': top_farmers,
        'recent_orders': recent_orders,
    })


@login_required
def update_order_status(request, pk):
    from django.http import JsonResponse
    if request.method == 'POST':
        try:
            order = CustomerOrder.objects.get(pk=pk, vegetable__farmer=request.user)
            status = request.POST.get('status')
            if status in ['pending', 'confirmed', 'delivered', 'cancelled']:
                order.status = status
                order.save(update_fields=['status'])
                return JsonResponse({'success': True})
        except CustomerOrder.DoesNotExist:
            pass
    return JsonResponse({'success': False})


def weather_view(request):
    weather_data = None
    error = None
    
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        
        if city:
            api_key = settings.WEATHER_API_KEY
            url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
            
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if response.status_code == 200:
                    weather_data = {
                        'city': data['name'],
                        'country': data['sys']['country'],
                        'temperature': round(data['main']['temp']),
                        'feels_like': round(data['main']['feels_like']),
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'wind_speed': data['wind']['speed'],
                        'description': data['weather'][0]['description'].title(),
                        'icon': data['weather'][0]['icon'],
                        'temp_min': round(data['main']['temp_min']),
                        'temp_max': round(data['main']['temp_max']),
                    }
                elif response.status_code == 401:
                    error = 'Invalid API key. Please check your OpenWeatherMap API key in settings.py'
                elif response.status_code == 404:
                    error = f'City "{city}" not found. Try: Kathmandu, Delhi, Mumbai, London, New York'
                else:
                    error = f'Error: {data.get("message", "Unable to fetch weather data")}'
            except requests.exceptions.Timeout:
                error = 'Request timeout. Please try again.'
            except requests.exceptions.ConnectionError:
                error = 'Connection error. Please check your internet connection.'
            except Exception as e:
                error = f'Error: {str(e)}'
        else:
            error = 'Please enter a city name.'
    
    return render(request, 'weather.html', {'weather_data': weather_data, 'error': error})


@login_required
def checkout_page(request):
    """Display checkout page with shipping address and order summary"""
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')
    
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    # Check if specific items are selected from cart
    selected_items_param = request.GET.get('items', '')
    if selected_items_param:
        try:
            selected_item_ids = list(map(int, selected_items_param.split(',')))
            cart_items = cart.items.filter(id__in=selected_item_ids).select_related('vegetable').all()
        except (ValueError, AttributeError):
            cart_items = cart.items.select_related('vegetable').all()
    else:
        # Show all items if coming from "Buy Now" product page
        cart_items = cart.items.select_related('vegetable').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    # Calculate totals
    items_total = sum(float(item.subtotal()) for item in cart_items)
    delivery_fee = 150
    total_price = items_total + delivery_fee
    
    # eSewa Integration variables
    esewa_merchant_code = "EPAYTEST"
    esewa_secret_key = "8gBm/:&EnhH.1/q"

    # Always generate a fresh UUID so eSewa never sees a duplicate
    transaction_uuid = str(uuid.uuid4())
    request.session['esewa_transaction_uuid'] = transaction_uuid
    request.session['esewa_total_price'] = total_price

    # Sign message
    total_price_int = round(total_price)
    message = f"total_amount={total_price_int},transaction_uuid={transaction_uuid},product_code={esewa_merchant_code}"
    hash_obj = hmac.new(
        esewa_secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    esewa_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    domain = request.build_absolute_uri('/')[:-1]
    
    # Handle selected address for display - check URL param first, then session
    selected_address = request.GET.get('selected_address') or request.session.get('checkout_selected_address', 'address')

    # Determine which address to display based on selection
    user_profile = request.user.userprofile
    if selected_address == 'address2' and user_profile.address2:
        display_address = user_profile.address2
        display_phone = user_profile.phone_number
        display_address_type = "ADDRESS 1"
    elif selected_address == 'address3' and user_profile.address3:
        display_address = user_profile.address3
        display_phone = user_profile.phone_number
        display_address_type = "ADDRESS 2"
    else:
        selected_address = 'address'
        display_address = user_profile.address
        display_phone = user_profile.phone_number
        display_address_type = "DEFAULT"

    context = {
        'cart_items': cart_items,
        'items_total': items_total,
        'delivery_fee': delivery_fee,
        'total_price': total_price_int,
        'selected_items_param': selected_items_param,
        'esewa_merchant_code': esewa_merchant_code,
        'transaction_uuid': transaction_uuid,
        'esewa_signature': esewa_signature,
        'domain': domain,
        'display_address': display_address,
        'display_phone': display_phone,
        'display_address_type': display_address_type,
        'selected_address': selected_address,
    }
    
    return render(request, 'dashboard/checkout.html', context)


@login_required
def update_checkout_address(request):
    """Update user address during checkout"""
    if request.method == 'POST':
        selected_address = request.POST.get('selected_address', '')
        items_param = request.POST.get('items', '')  # Preserve items parameter

        # Build redirect URL with items parameter if present
        redirect_url = reverse('checkout_page')
        params = []
        if items_param:
            params.append(f'items={items_param}')
        if params:
            redirect_url += '?' + '&'.join(params)

        user_profile = request.user.userprofile

        if selected_address == 'new_address':
            # Handle new address addition
            new_address = request.POST.get('new_address', '').strip()
            if not new_address:
                messages.error(request, 'New address is required')
                return HttpResponseRedirect(redirect_url)

            # Save to the next available address slot in profile
            if not user_profile.address2:
                user_profile.address2 = new_address
                user_profile.save()
                selected_address = 'address2'
                request.session['checkout_selected_address'] = 'address2'
                messages.success(request, 'New address added as Address 1.')
            elif not user_profile.address3:
                user_profile.address3 = new_address
                user_profile.save()
                selected_address = 'address3'
                request.session['checkout_selected_address'] = 'address3'
                messages.success(request, 'New address added as Address 2.')
            else:
                messages.error(request, 'You already have 3 addresses. Please manage your addresses in your profile.')
                return HttpResponseRedirect(redirect_url)

        elif selected_address in ['address', 'address2', 'address3']:
            # Just store the selection in session, never modify any address field
            request.session['checkout_selected_address'] = selected_address
            messages.success(request, 'Delivery address selected for this order.')

        else:
            messages.error(request, 'Please select an address option')
            return HttpResponseRedirect(redirect_url)

        request.session['checkout_selected_address'] = selected_address
        return HttpResponseRedirect(f"{redirect_url}&selected_address={selected_address}" if '?' in redirect_url else f"{redirect_url}?selected_address={selected_address}")

    return redirect('checkout_page')


@login_required
def cancel_order(request, pk):
    """Allow customer to cancel a pending order."""
    from django.http import JsonResponse
    order = get_object_or_404(CustomerOrder, pk=pk, customer=request.user)
    if order.status not in ['pending', 'confirmed']:
        return JsonResponse({'success': False, 'message': 'Order cannot be cancelled.'})
    # Restore vegetable stock
    order.vegetable.quantity += order.quantity
    order.vegetable.available = True
    order.vegetable.save()
    order.status = 'cancelled'
    order.save()
    return JsonResponse({'success': True, 'message': 'Order cancelled successfully.'})


def feedback_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        rating = request.POST.get('rating')
        message = request.POST.get('message')
        
        if full_name and email and rating and message:
            Feedback.objects.create(
                full_name=full_name,
                email=email,
                rating=int(rating),
                message=message
            )
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback')
        else:
            messages.error(request, 'Please fill all fields')
    
    feedbacks = Feedback.objects.all()[:10]  # Get 10 most recent feedbacks
    return render(request, 'feedback.html', {'feedbacks': feedbacks})


@login_required
def farmer_orders(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    
    # Mark all unviewed orders as viewed when farmer visits this page
    CustomerOrder.objects.filter(
        vegetable__farmer=request.user,
        viewed_by_farmer=False
    ).update(viewed_by_farmer=True)
    
    # Get all customer orders for this farmer's vegetables
    orders = CustomerOrder.objects.filter(vegetable__farmer=request.user).select_related('customer', 'vegetable').order_by('-ordered_at')
    
    for o in orders:
        o.product_name = o.vegetable.name
        o.unit_price = o.vegetable.price_per_unit
        o.buyer_name = f"{o.customer.first_name} {o.customer.last_name}"
        o.buyer_phone = o.customer.userprofile.phone_number
        o.buyer_address = o.shipping_address or o.customer.userprofile.address
        o.order_date = o.ordered_at
    
    all_orders = orders
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    if status_filter:
        all_orders = [o for o in all_orders if o.status == status_filter]
    
    # Calculate summary stats
    co_orders = CustomerOrder.objects.filter(vegetable__farmer=request.user).count()
    total_orders = co_orders
    
    co_revenue = CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['confirmed', 'delivered']).aggregate(total=Sum('total_price'))['total'] or 0
    total_revenue = co_revenue
    
    co_pending = CustomerOrder.objects.filter(vegetable__farmer=request.user, status='pending').count()
    pending_orders_count = co_pending
    
    co_conf = CustomerOrder.objects.filter(vegetable__farmer=request.user, status='confirmed').count()
    confirmed_orders_count = co_conf
    
    context = {
        'orders': all_orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders_count,
        'confirmed_orders': confirmed_orders_count,
        'status_filter': status_filter,
        'new_orders_count': CustomerOrder.objects.filter(vegetable__farmer=request.user, status__in=['pending', 'confirmed'], viewed_by_farmer=False).count(),
    }
    return render(request, 'dashboard/farmer_orders.html', context)


def download_farmer_order_receipt(request, pk):
    """Generate and download farmer order receipt as PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    from django.http import HttpResponse
    
    # Get the order
    order = get_object_or_404(CustomerOrder, id=pk, vegetable__farmer=request.user)
    buyer_name = f"{order.customer.first_name} {order.customer.last_name}"
    order_date = order.ordered_at
    product_name = order.vegetable.name
    buyer_role = "Customer"
        
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#22C55E'),
        spaceAfter=6,
        alignment=1  # Center
    )
    
    # Title
    elements.append(Paragraph('KrishiConnect', title_style))
    elements.append(Paragraph('Sale Receipt (Farmer Copy)', styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Order details table
    order_data = [
        ['Order ID:', '#' + str(order.id), 'Date:', order_date.strftime('%b %d, %Y') if order_date else 'N/A'],
        ['Product:', product_name, 'Buyer:', buyer_name],
        ['Total Amount:', '₹' + str(order.total_price), '', ''],
    ]
    
    order_table = Table(order_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 2*inch])
    order_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 11),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    elements.append(Paragraph('Thank you for choosing KrishiConnect!', styles['Italic']))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF from buffer
    file_data = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order_type}{pk}.pdf"'
    response.write(file_data)
    return response


@login_required
def farmer_analytics(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    from django.db.models import Count
    vegetables = Vegetable.objects.filter(farmer=request.user)
    orders = CustomerOrder.objects.filter(vegetable__farmer=request.user)
    total_earnings = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = orders.count()
    total_products = vegetables.count()
    available_products = vegetables.filter(available=True).count()
    top_products = list(orders.values('vegetable__name').annotate(total_qty=Sum('quantity'), total_revenue=Sum('total_price')).order_by('-total_revenue')[:5])
    category_breakdown = list(vegetables.values('category').annotate(count=Count('id')).order_by('-count'))
    context = {
        'total_earnings': total_earnings,
        'total_orders': total_orders,
        'total_products': total_products,
        'available_products': available_products,
        'top_products': top_products,
        'category_breakdown': category_breakdown,
    }
    return render(request, 'dashboard/farmer_analytics.html', context)


@login_required
def customer_analytics(request):
    if request.user.userprofile.role != 'customer':
        return redirect('customer_dashboard')
    from django.db.models import Count
    orders = CustomerOrder.objects.filter(customer=request.user)
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = orders.count()
    pending = orders.filter(status='pending').count()
    confirmed = orders.filter(status='confirmed').count()
    delivered = orders.filter(status='delivered').count()
    top_products = list(orders.values('vegetable__name').annotate(total_qty=Sum('quantity'), total_spent=Sum('total_price')).order_by('-total_spent')[:5])
    category_spending = list(orders.values('vegetable__category').annotate(total=Sum('total_price')).order_by('-total'))
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    context = {
        'total_spent': total_spent,
        'total_orders': total_orders,
        'pending': pending,
        'confirmed': confirmed,
        'delivered': delivered,
        'top_products': top_products,
        'category_spending': category_spending,
        'cart': cart,
    }
    return render(request, 'dashboard/customer_analytics.html', context)


def custom_password_reset(request):
    from django.contrib.auth.forms import PasswordResetForm
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.contrib.auth.models import User

    if request.method == 'POST':
        username_or_email = request.POST.get('email', '').strip()
        print(f'DEBUG: email entered = {username_or_email}')

        # Find user by username or email
        user = None
        try:
            user = User.objects.get(email=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                pass

        print(f'DEBUG: user found = {user}')

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            reset_url = f"{protocol}://{domain}/password-reset-confirm/{uid}/{token}/"
            print(f'DEBUG: sending email to {settings.EMAIL_HOST_USER}')

            send_mail(
                subject='Reset Password - Krishi Connect',
                message=f'Hello {user.username},\n\nReset your password here:\n{reset_url}\n\nExpires in 24 hours.\n\n- Krishi Connect Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            print('DEBUG: email sent successfully')

        return redirect('password_reset_done')

    return render(request, 'registration/password_reset.html')
