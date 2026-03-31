from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import requests
from django.conf import settings
from .models import UserProfile, Vegetable, SupplierPurchase, SupplierInventory, CustomerOrder, Cart, CartItem
from django.db.models import Sum, Avg
from django.db import models

def home(request):
    return render(request, 'home.html')

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
    context = {
        'user_role': user_profile.role,
        'user_profile': user_profile
    }
    
    if user_profile.role == 'farmer':
        vegetables = Vegetable.objects.filter(farmer=request.user)
        total_vegetables = vegetables.count()
        available_vegetables = vegetables.filter(available=True).count()
        sold_out = vegetables.filter(available=False).count()
        total_earnings = SupplierPurchase.objects.filter(vegetable__farmer=request.user).aggregate(total=Sum('total_price'))['total'] or 0
        recent_purchases = SupplierPurchase.objects.filter(vegetable__farmer=request.user).order_by('-purchased_at')[:5]
        context.update({
            'vegetables': vegetables,
            'total_vegetables': total_vegetables,
            'available_vegetables': available_vegetables,
            'sold_out': sold_out,
            'total_earnings': total_earnings,
            'recent_purchases': recent_purchases,
        })
        return render(request, 'dashboard/farmer_dashboard.html', context)
    elif user_profile.role == 'expert':
        return render(request, 'dashboard/expert_dashboard.html', context)
    elif user_profile.role == 'supplier':
        purchases = SupplierPurchase.objects.filter(supplier=request.user)
        inventory = SupplierInventory.objects.filter(supplier=request.user)
        context['purchases'] = purchases
        context['inventory'] = inventory
        return render(request, 'dashboard/supplier_dashboard.html', context)
    elif user_profile.role == 'customer':
        orders = CustomerOrder.objects.filter(customer=request.user)
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        recommended = Vegetable.objects.filter(available=True).order_by('-created_at')[:3]
        context['orders'] = orders
        context['total_spent'] = total_spent
        context['recommended'] = recommended
        return render(request, 'dashboard/customer_dashboard.html', context)
    else:
        return render(request, 'dashboard.html', context)

def about(request):
    return render(request, 'about.html')

def blog(request):
    return render(request, 'blog.html')

def solutions(request):
    return render(request, 'solutions.html')


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
    return render(request, 'dashboard/farmer_products.html', {'vegetables': vegetables})

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
            quantity=request.POST['quantity'],
            unit=request.POST['unit'],
            price_per_unit=request.POST['price_per_unit'],
            description=request.POST.get('description', ''),
            image=request.FILES.get('image')
        )
        messages.success(request, 'Vegetable added successfully')
        return redirect('dashboard')
    return render(request, 'dashboard/add_vegetable.html')

@login_required
def edit_vegetable(request, pk):
    vegetable = get_object_or_404(Vegetable, pk=pk, farmer=request.user)
    if request.method == 'POST':
        vegetable.name = request.POST['name']
        vegetable.category = request.POST.get('category', vegetable.category)
        vegetable.quantity = request.POST['quantity']
        vegetable.unit = request.POST['unit']
        vegetable.price_per_unit = request.POST['price_per_unit']
        vegetable.description = request.POST.get('description', '')
        if request.FILES.get('image'):
            vegetable.image = request.FILES['image']
        vegetable.available = request.POST.get('available') == 'on'
        vegetable.save()
        messages.success(request, 'Product updated successfully')
        return redirect('dashboard')
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
    return redirect('dashboard')

def public_marketplace(request):
    vegetables = Vegetable.objects.filter(available=True)
    return render(request, 'marketplace.html', {'vegetables': vegetables})

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
        return redirect('dashboard')

    return redirect('product_detail', pk=pk)

@login_required
def add_to_cart(request, pk):
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can add to cart')
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

        cart, _ = Cart.objects.get_or_create(customer=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, vegetable=vegetable)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
        messages.success(request, f'{vegetable.name} added to cart!')

    return redirect('product_detail', pk=pk)

@login_required
def cart_view(request):
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    return render(request, 'cart.html', {'cart': cart})

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart')
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
    
    inventory = SupplierInventory.objects.filter(available=True)
    return render(request, 'dashboard/customer_marketplace.html', {'inventory': inventory})

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
    
    return render(request, 'dashboard/order_vegetable.html', {'inventory': inventory})

# Weather View
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
