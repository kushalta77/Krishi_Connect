from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from .models import UserProfile

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
        
        if role not in ['farmer', 'expert']:
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
        return render(request, 'dashboard/farmer_dashboard.html', context)
    elif user_profile.role == 'expert':
        return render(request, 'dashboard/supplier_dashboard.html', context)
    else:
        return render(request, 'dashboard.html', context)

def about(request):
    return render(request, 'about.html')

def blog(request):
    return render(request, 'blog.html')

def solutions(request):
    return render(request, 'solutions.html')