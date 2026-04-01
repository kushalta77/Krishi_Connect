from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Product, Category, Order
from .forms import ProductForm, OrderForm


# ── Farmer Views ──────────────────────────────────────────────────────────────

@login_required
def add_product(request):
    """Allows a logged-in farmer to list a new product for sale."""
    if request.user.userprofile.role != 'farmer':
        messages.error(request, 'Only farmers can list products.')
        return redirect('dashboard')

    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.farmer = request.user   # auto-assign farmer from session
        product.save()
        messages.success(request, f'"{product.name}" listed successfully!')
        return redirect('marketplace')

    return render(request, 'products/add_product.html', {'form': form})


@login_required
def my_products(request):
    """Farmer's own product listings."""
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')

    products = Product.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'products/my_products.html', {'products': products})


# ── Customer / Public Views ───────────────────────────────────────────────────

def marketplace(request):
    """Public grid of all available products, filterable by category."""
    categories = Category.objects.all()
    products = Product.objects.filter(stock_quantity__gt=0).select_related('farmer', 'category')

    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    return render(request, 'products/marketplace.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
    })


def product_detail(request, pk):
    """Detail page for a single product with an order form for customers."""
    product = get_object_or_404(Product, pk=pk)
    form = None

    if request.user.is_authenticated and request.user.userprofile.role == 'customer':
        form = OrderForm(product=product)

    return render(request, 'products/product_detail.html', {
        'product': product,
        'form': form,
    })


@login_required
def place_order(request, pk):
    """Handles order submission and decreases product stock atomically."""
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can place orders.')
        return redirect('marketplace')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = OrderForm(product=product, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Re-fetch with lock to prevent race conditions
                product = Product.objects.select_for_update().get(pk=pk)
                qty = form.cleaned_data['quantity']

                if qty > product.stock_quantity:
                    messages.error(request, 'Not enough stock available.')
                    return redirect('product_detail', pk=pk)

                # Create order
                Order.objects.create(
                    customer=request.user,
                    product=product,
                    quantity=qty,
                )

                # Decrease stock
                product.stock_quantity -= qty
                product.save()

            messages.success(request, f'Order placed for {qty} kg of {product.name}!')
            return redirect('my_orders')
        else:
            messages.error(request, 'Invalid order. Please check the quantity.')
            return redirect('product_detail', pk=pk)

    return redirect('product_detail', pk=pk)


@login_required
def my_orders(request):
    """Customer's order history."""
    if request.user.userprofile.role != 'customer':
        return redirect('dashboard')

    orders = Order.objects.filter(customer=request.user).select_related('product').order_by('-ordered_at')
    status_filter = request.GET.get('status', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    return render(request, 'products/my_orders.html', {
        'orders': orders,
        'status_filter': status_filter
    })
