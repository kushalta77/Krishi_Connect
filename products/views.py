from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Product, Category, Order, Cart, CartItem
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
    """Handles order submission with delivery details and decreases product stock atomically."""
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
                delivery_address = form.cleaned_data['delivery_address']
                phone_number = form.cleaned_data['phone_number']
                delivery_mode = form.cleaned_data['delivery_mode']

                if not product.can_fulfill_order(qty):
                    messages.error(request, f'Order must be between {product.min_order_qty} and {product.stock_quantity} {product.unit}.')
                    return redirect('product_detail', pk=pk)

                # Create order with delivery info
                order = Order.objects.create(
                    customer=request.user,
                    product=product,
                    quantity=qty,
                    delivery_address=delivery_address,
                    phone_number=phone_number,
                    delivery_mode=delivery_mode,
                    status='pending',  # Awaiting farmer acceptance
                )

                # Decrease stock immediately
                product.stock_quantity -= qty
                product.save()

            messages.success(request, f'✓ Order placed! Farmer will review shortly.')
            return redirect('my_orders')
        else:
            messages.error(request, 'Invalid order. ' + ', '.join(form.errors.get('__all__', [])))
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


# ── Farmer Order Management ───────────────────────────────────────────────────

@login_required
def incoming_orders(request):
    """Farmer view of all pending/incoming orders for their products."""
    if request.user.userprofile.role != 'farmer':
        messages.error(request, 'Only farmers can view incoming orders.')
        return redirect('dashboard')

    # Get all orders for products this farmer listed
    orders = Order.objects.filter(
        product__farmer=request.user
    ).select_related('customer', 'product').order_by('-ordered_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    return render(request, 'products/incoming_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
    })


@login_required
def manage_order(request, order_id):
    """Farmer accepts/rejects/ships/delivers an order."""
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, product__farmer=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        notes = request.POST.get('farmer_notes', '')
        
        from django.utils import timezone

        if action == 'accept' and order.status == 'pending':
            order.status = 'accepted'
            order.accepted_at = timezone.now()
            order.farmer_notes = notes
            order.save()
            messages.success(request, '✓ Order accepted!')
            
        elif action == 'reject' and order.status == 'pending':
            order.status = 'rejected'
            order.farmer_notes = notes
            order.save()
            # Restore stock since order was rejected
            order.product.stock_quantity += order.quantity
            order.product.save()
            messages.warning(request, 'Order rejected & stock restored.')
            
        elif action == 'ship' and order.status == 'accepted':
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.save()
            messages.success(request, '✓ Order marked as shipped!')
            
        elif action == 'deliver' and order.status == 'shipped':
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.save()
            messages.success(request, '✓ Order delivered!')
        
        return redirect('incoming_orders')

    return render(request, 'products/manage_order.html', {'order': order})


# ── Shopping Cart Views ───────────────────────────────────────────────────────

@login_required
def view_bulk_cart(request):
    """View shopping cart for bulk orders."""
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can access cart.')
        return redirect('marketplace')
    
    cart, _ = Cart.objects.get_or_create(customer=request.user)
    
    return render(request, 'products/bulk_cart.html', {'cart': cart})


@login_required
def add_to_bulk_cart(request, pk):
    """Add product to cart. First add must respect minimum quantity."""
    if request.user.userprofile.role != 'customer':
        messages.error(request, 'Only customers can add to cart.')
        return redirect('marketplace')
    
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    if request.method == 'POST':
        qty_str = request.POST.get('quantity', '0')
        try:
            qty = float(qty_str)
        except ValueError:
            messages.error(request, 'Invalid quantity.')
            return redirect('product_detail', pk=pk)
        
        # Get or create cart
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        
        # Check if product already in cart
        existing_item = cart.items.filter(product=product).first()
        
        if existing_item:
            # Item already in cart - allow increment by any amount >= 1
            if qty < 1:
                messages.error(request, f'Increment must be at least 1 {product.unit}.')
                return redirect('product_detail', pk=pk)
            
            # Check stock before updating
            new_qty = existing_item.quantity + qty
            if new_qty > product.stock_quantity:
                messages.error(request, f'Only {product.stock_quantity} {product.unit} available.')
                return redirect('product_detail', pk=pk)
            
            existing_item.quantity = new_qty
            existing_item.save()
            messages.success(request, f'✓ Updated {product.name} to {new_qty} {product.unit}.')
        else:
            # First time adding - must respect minimum
            if qty < product.min_order_qty:
                messages.error(request, f'Minimum order is {product.min_order_qty} {product.unit}.')
                return redirect('product_detail', pk=pk)
            
            if qty > product.stock_quantity:
                messages.error(request, f'Only {product.stock_quantity} {product.unit} available.')
                return redirect('product_detail', pk=pk)
            
            # Create cart item
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=qty
            )
            messages.success(request, f'✓ Added {product.name} to cart ({qty} {product.unit}).')
        
        return redirect('view_bulk_cart')
    
    return redirect('product_detail', pk=pk)


@login_required
def update_cart_item(request, item_id):
    """Update quantity of item in cart. Can increment/decrement by any amount >= 1."""
    if request.user.userprofile.role != 'customer':
        return redirect('marketplace')
    
    item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        qty_str = request.POST.get('quantity', '')
        
        if action == 'update' and qty_str:
            try:
                new_qty = float(qty_str)
            except ValueError:
                messages.error(request, 'Invalid quantity.')
                return redirect('view_bulk_cart')
            
            # Allow updates >= 1, must also be >= minimum
            if new_qty < item.product.min_order_qty:
                messages.error(request, f'Quantity must be at least {item.product.min_order_qty} {item.product.unit}.')
                return redirect('view_bulk_cart')
            
            if new_qty > item.product.stock_quantity:
                messages.error(request, f'Only {item.product.stock_quantity} {item.product.unit} available.')
                return redirect('view_bulk_cart')
            
            item.quantity = new_qty
            item.save()
            messages.success(request, f'✓ Updated to {new_qty} {item.product.unit}.')
        
        elif action == 'remove':
            product_name = item.product.name
            item.delete()
            messages.warning(request, f'Removed {product_name} from cart.')
        
        return redirect('view_bulk_cart')
    
    return redirect('view_bulk_cart')


@login_required
def checkout_bulk_cart(request):
    """Checkout all items in cart and create orders."""
    if request.user.userprofile.role != 'customer':
        return redirect('marketplace')
    
    cart = get_object_or_404(Cart, customer=request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('view_bulk_cart')
    
    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        delivery_mode = request.POST.get('delivery_mode', 'delivery')
        
        if not delivery_address or not phone_number:
            messages.error(request, 'Please provide delivery address and phone number.')
            return redirect('view_bulk_cart')
        
        try:
            with transaction.atomic():
                orders_created = 0
                for cart_item in cart.items.all():
                    product = Product.objects.select_for_update().get(pk=cart_item.product_id)
                    qty = cart_item.quantity
                    
                    # Final validation
                    if not product.can_fulfill_order(qty):
                        raise ValueError(f'{product.name}: Order must be between {product.min_order_qty} and {product.stock_quantity} {product.unit}.')
                    
                    if qty > product.stock_quantity:
                        raise ValueError(f'{product.name}: Only {product.stock_quantity} {product.unit} available.')
                    
                    # Create order
                    Order.objects.create(
                        customer=request.user,
                        product=product,
                        quantity=qty,
                        delivery_address=delivery_address,
                        phone_number=phone_number,
                        delivery_mode=delivery_mode,
                        status='pending'
                    )
                    
                    # Decrease stock
                    product.stock_quantity -= qty
                    product.save()
                    orders_created += 1
                
                # Clear cart
                cart.items.all().delete()
                messages.success(request, f'✓ {orders_created} order(s) placed successfully!')
                return redirect('my_orders')
        
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('view_bulk_cart')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('view_bulk_cart')
    
    return render(request, 'products/checkout_bulk_cart.html', {'cart': cart})
