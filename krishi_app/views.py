from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
import re
import requests
from django.conf import settings
from .models import UserProfile, Vegetable, SupplierPurchase, SupplierInventory, CustomerOrder, Cart, CartItem, Feedback
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
        
        if role not in ['farmer', 'expert', 'supplier', 'customer']:
            errors.append('Invalid role selected.')
        
        if profile_image:
            if profile_image.size > 5 * 1024 * 1024:
                errors.append('Profile image size must be less than 5MB.')
            
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if profile_image.content_type not in allowed_types:
                errors.append('Profile image must be a JPEG, PNG, or GIF file.')
        
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
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            UserProfile.objects.create(
                user=user,
                role=role,
                profile_image=profile_image
            )
            
            messages.success(request, 'Registration successful! Please login to continue.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'An error occurred during registration. Please try again.')
            context = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
            }
            return render(request, 'registration/register.html', context)
    
    return render(request, 'registration/register.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logged out successfully')
        return redirect('home')
    return redirect('home')

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
        total_earnings = SupplierPurchase.objects.filter(vegetable__farmer=request.user).aggregate(total=Sum('total_price'))['total'] or 0
        total_orders = SupplierPurchase.objects.filter(vegetable__farmer=request.user).count()
        recent_purchases = SupplierPurchase.objects.filter(vegetable__farmer=request.user).order_by('-purchased_at')[:5]
        context = {
            'user_role': user_profile.role,
            'user_profile': user_profile,
            'vegetables': vegetables,
            'total_vegetables': total_vegetables,
            'available_vegetables': available_vegetables,
            'sold_out': sold_out,
            'total_earnings': total_earnings,
            'total_orders': total_orders,
            'recent_purchases': recent_purchases,
        }
        return render(request, 'dashboard/farmer_dashboard.html', context)
    elif user_profile.role == 'expert':
        return render(request, 'dashboard/expert_dashboard.html', {'user_role': user_profile.role})
    elif user_profile.role == 'supplier':
        purchases = SupplierPurchase.objects.filter(supplier=request.user)
        inventory = SupplierInventory.objects.filter(supplier=request.user)
        return render(request, 'dashboard/supplier_dashboard.html', {
            'user_role': user_profile.role,
            'purchases': purchases,
            'inventory': inventory,
        })
    return redirect('home')

@login_required
def customer_dashboard(request):
    """Customer dashboard view at /customer/dashboard/"""
    user_profile = request.user.userprofile
    orders = CustomerOrder.objects.filter(customer=request.user)
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    recommended = Vegetable.objects.filter(available=True).order_by('-created_at')[:3]
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    context = {
        'user_role': user_profile.role,
        'user_profile': user_profile,
        'orders': orders,
        'total_spent': total_spent,
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
    return render(request, 'dashboard/farmer_profile.html', {'profile': profile})


# Farmer Views
@login_required
def farmer_stock(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    vegetables = Vegetable.objects.filter(farmer=request.user, available=True).order_by('-created_at')
    total_quantity = vegetables.aggregate(total=Sum('quantity'))['total'] or 0
    avg_price = vegetables.aggregate(avg=models.Avg('price_per_unit'))['avg'] or 0
    return render(request, 'dashboard/farmer_stock.html', {
        'vegetables': vegetables,
        'total_quantity': total_quantity,
        'avg_price': avg_price,
    })

@login_required
def farmer_products(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    vegetables = Vegetable.objects.filter(farmer=request.user).order_by('-created_at')
    paginator = Paginator(vegetables, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/farmer_products.html', {'vegetables': page_obj, 'paginator': paginator})

@login_required
def add_vegetable(request):
    if request.user.userprofile.role != 'farmer':
        messages.error(request, 'Only farmers can add vegetables')
        return redirect('dashboard')
    
    if request.method == 'POST':
        Vegetable.objects.create(
            farmer=request.user,
            name=request.POST['name'],
            category=request.POST.get('category', 'vegetable'),
            quantity=request.POST.get('stock') or request.POST.get('quantity'),
            unit=request.POST['unit'],
            base_price=request.POST.get('base_price') or request.POST['price_per_unit'],
            price_per_unit=request.POST['price_per_unit'],
            discount_price=request.POST.get('discount_price') or None,
            harvest_date=request.POST.get('harvest_date') or None,
            shelf_life_days=request.POST.get('shelf_life_days') or 7,
            is_farmers_special=request.POST.get('is_farmers_special') == 'on',
            description=request.POST.get('description', ''),
            image=request.FILES.get('image')
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
        messages.success(request, 'Product updated successfully')
        return redirect('farmer_products')
    return render(request, 'dashboard/edit_vegetable.html', {'vegetable': vegetable})

@login_required
def view_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    return render(request, 'dashboard/view_vegetable.html', {'vegetable': vegetable})

@login_required
def delete_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    vegetable.delete()
    messages.success(request, 'Vegetable deleted successfully')
    return redirect('farmer_products')

def public_marketplace(request):
    q = request.GET.get('q', '')
    vegetables = Vegetable.objects.filter(available=True)
    return render(request, 'marketplace.html', {'vegetables': vegetables, 'search_query': q})

def product_detail(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)
    return render(request, 'product_detail.html', {'vegetable': vegetable})

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

        # Create a temporary SupplierInventory entry to reuse CustomerOrder model
        inv, _ = SupplierInventory.objects.get_or_create(
            supplier=vegetable.farmer,
            vegetable_name=vegetable.name,
            defaults={
                'quantity': vegetable.quantity,
                'unit': vegetable.unit,
                'price_per_unit': vegetable.price_per_unit,
                'image': vegetable.image,
            }
        )

        total_price = quantity * float(vegetable.price_per_unit)
        CustomerOrder.objects.create(
            customer=request.user,
            supplier_inventory=inv,
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
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can add to cart')
        return redirect('login')

    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)

    if request.method == 'POST':
        try:
            quantity = float(request.POST.get('quantity', '1').strip())
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity')
            return redirect('customer_marketplace')
        
        # Edge case: Validate quantity is positive
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('customer_marketplace')
        
        # Edge case: Check stock availability
        if quantity > float(vegetable.quantity):
            messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} available')
            return redirect('customer_marketplace')
        
        # Add to cart
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        try:
            item = CartItem.objects.get(cart=cart, vegetable=vegetable)
            # Edge case: Check if adding more would exceed available stock
            if item.quantity + quantity > float(vegetable.quantity):
                messages.warning(request, f'Maximum available for {vegetable.name} is {vegetable.quantity} {vegetable.unit}')
                return redirect('customer_marketplace')
            item.quantity += quantity
        except CartItem.DoesNotExist:
            item = CartItem(cart=cart, vegetable=vegetable, quantity=quantity)
        
        item.save()
        messages.success(request, f'{vegetable.name} added to cart! (Qty: {item.quantity} {vegetable.unit})')
        # Redirect back to customer marketplace
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
def decrease_cart_quantity(request, pk):
    """Decrease the quantity of a cart item, or remove it if quantity reaches 0."""
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
        messages.success(request, f'Decreased quantity of {item.vegetable.name}')
    else:
        # Remove item if quantity would become 0
        item_name = item.vegetable.name
        item.delete()
        messages.success(request, f'{item_name} removed from cart')
    
    return redirect('cart')

@login_required
def buy_now_action(request, pk):
    """Add product to cart and redirect to cart page (for 'Buy Now' button)."""
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can buy products')
        return redirect('login')

    vegetable = get_object_or_404(Vegetable, pk=pk, available=True)

    if request.method == 'POST':
        try:
            quantity = float(request.POST.get('quantity', '1').strip())
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity')
            return redirect('customer_marketplace')
        
        # Edge case: Validate quantity
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('customer_marketplace')
        
        # Edge case: Check stock availability
        if quantity > float(vegetable.quantity):
            messages.error(request, f'Only {vegetable.quantity} {vegetable.unit} of {vegetable.name} available')
            return redirect('customer_marketplace')
        
        # Add to cart (duplicate products will increase quantity automatically)
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        try:
            item = CartItem.objects.get(cart=cart, vegetable=vegetable)
            # Check if adding more quantity would exceed stock
            if item.quantity + quantity > float(vegetable.quantity):
                messages.warning(request, f'You already have {item.quantity} {vegetable.unit} of this. Only {vegetable.quantity} available total.')
                return redirect('cart')
            item.quantity += quantity
        except CartItem.DoesNotExist:
            item = CartItem(cart=cart, vegetable=vegetable, quantity=quantity)
        
        item.save()
        messages.success(request, f'{quantity} {vegetable.unit} of {vegetable.name} added to cart!')
        # Redirect to cart page immediately
        return redirect('cart')
    
    return redirect('customer_marketplace')

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
    for item in items:
        inv, _ = SupplierInventory.objects.get_or_create(
            supplier=item.vegetable.farmer,
            vegetable_name=item.vegetable.name,
            defaults={
                'quantity': item.vegetable.quantity,
                'unit': item.vegetable.unit,
                'price_per_unit': item.vegetable.price_per_unit,
                'image': item.vegetable.image,
            }
        )
        CustomerOrder.objects.create(
            customer=request.user,
            supplier_inventory=inv,
            quantity=item.quantity,
            total_price=item.quantity * item.vegetable.price_per_unit
        )
        item.vegetable.quantity -= item.quantity
        if item.vegetable.quantity <= 0:
            item.vegetable.available = False
        item.vegetable.save()
    cart.items.all().delete()
    messages.success(request, 'All orders placed successfully!')
    return redirect('dashboard')

# Supplier Views
@login_required
def supplier_marketplace(request):
    if request.user.userprofile.role != 'supplier':
        messages.error(request, 'Only suppliers can access this page')
        return redirect('dashboard')
    
    vegetables = Vegetable.objects.filter(available=True)
    return render(request, 'dashboard/supplier_marketplace.html', {'vegetables': vegetables})

@login_required
def purchase_from_farmer(request, pk):
    if request.user.userprofile.role != 'supplier':
        messages.error(request, 'Only suppliers can purchase')
        return redirect('dashboard')
    
    vegetable = get_object_or_404(Vegetable, pk=pk)
    
    if request.method == 'POST':
        quantity = float(request.POST['quantity'])
        total_price = quantity * float(vegetable.price_per_unit)
        
        SupplierPurchase.objects.create(
            supplier=request.user,
            vegetable=vegetable,
            quantity=quantity,
            total_price=total_price
        )
        
        SupplierInventory.objects.create(
            supplier=request.user,
            vegetable_name=vegetable.name,
            quantity=quantity,
            unit=vegetable.unit,
            price_per_unit=float(vegetable.price_per_unit) * 1.2,
            image=vegetable.image
        )
        
        vegetable.quantity -= quantity
        if vegetable.quantity <= 0:
            vegetable.available = False
        vegetable.save()
        
        messages.success(request, 'Purchase successful')
        return redirect('supplier_marketplace')
    
    return render(request, 'dashboard/purchase_vegetable.html', {'vegetable': vegetable})

# Customer Views
@login_required
def customer_marketplace(request):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can access this page')
        return redirect('dashboard')
    
    q = request.GET.get('q', '')
    
    # Get all available products from Vegetable
    vegetables = list(Vegetable.objects.filter(available=True))
    
    # Get all available products from SupplierInventory
    inventory = list(SupplierInventory.objects.filter(available=True))
    
    # Filter by search query
    if q:
        vegetables = [v for v in vegetables if q.lower() in v.name.lower()]
        inventory = [i for i in inventory if q.lower() in i.vegetable_name.lower()]
    
    # Mark source type and add necessary attributes for template compatibility
    for v in vegetables:
        v.source = 'vegetable'
        v.vegetable_name = v.name
        v.supplier_first_name = v.farmer.first_name
        v.supplier_last_name = v.farmer.last_name
        v.supplier_id = v.farmer.id
    
    for i in inventory:
        i.source = 'inventory'
        i.supplier_first_name = i.supplier.first_name
        i.supplier_last_name = i.supplier.last_name
        i.supplier_id = i.supplier.id
    
    # Combine both lists
    combined_products = vegetables + inventory
    
    # Create a custom paginator for combined results
    paginator = Paginator(combined_products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get cart for floating icon
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    return render(request, 'dashboard/dashboard_marketplace.html', {'page_obj': page_obj, 'search_query': q, 'paginator': paginator, 'cart': cart})

@login_required
def order_from_supplier(request, pk):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can order')
        return redirect('dashboard')
    
    inventory = get_object_or_404(SupplierInventory, pk=pk)
    
    if request.method == 'POST':
        quantity = float(request.POST['quantity'])
        total_price = quantity * float(inventory.price_per_unit)
        
        CustomerOrder.objects.create(
            customer=request.user,
            supplier_inventory=inventory,
            quantity=quantity,
            total_price=total_price
        )
        
        inventory.quantity -= quantity
        if inventory.quantity <= 0:
            inventory.available = False
        inventory.save()
        
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
    top_products = CustomerOrder.objects.values('supplier_inventory__vegetable_name').annotate(
        vegetable_name=models.F('supplier_inventory__vegetable_name'),
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:6]
    max_qty = max((p['total_qty'] for p in top_products), default=1)
    category_stats = Vegetable.objects.values('category').annotate(count=Count('id')).order_by('-count')
    top_farmers = Vegetable.objects.values('farmer__username').annotate(product_count=Count('id')).order_by('-product_count')[:5]
    recent_orders = CustomerOrder.objects.select_related('customer', 'supplier_inventory').order_by('-ordered_at')[:8]
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
    
    # Get all orders (purchases) made by suppliers from this farmer's vegetables
    orders = SupplierPurchase.objects.filter(vegetable__farmer=request.user).select_related('supplier', 'vegetable').order_by('-purchased_at')
    
    # Also get customer orders for this farmer's vegetables (through SupplierInventory)
    from django.db.models import Q
    customer_orders = CustomerOrder.objects.filter(
        supplier_inventory__supplier=request.user
    ).select_related('customer', 'supplier_inventory').order_by('-ordered_at')
    
    # Combine both types of orders
    all_orders = list(orders) + list(customer_orders)
    
    # Get status filter from query params
    status_filter = request.GET.get('status', '')
    if status_filter:
        all_orders = [o for o in all_orders if o.status == status_filter]
    
    # Calculate summary stats
    total_orders = SupplierPurchase.objects.filter(vegetable__farmer=request.user).count()
    total_revenue = SupplierPurchase.objects.filter(vegetable__farmer=request.user).aggregate(total=Sum('total_price'))['total'] or 0
    pending_orders_count = SupplierPurchase.objects.filter(vegetable__farmer=request.user, status='pending').count()
    confirmed_orders_count = SupplierPurchase.objects.filter(vegetable__farmer=request.user, status='confirmed').count()
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders_count,
        'confirmed_orders': confirmed_orders_count,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/farmer_orders.html', context)
