from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('quintal', 'Quintal'),
        ('box', 'Box'),
        ('crate', 'Crate'),
    ]
    
    # Farmer who listed this product
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit (kg/box/etc)")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg', help_text="Unit type (kg, box, etc)")
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Available stock")
    min_order_qty = models.DecimalField(max_digits=10, decimal_places=2, default=5, help_text="Minimum order quantity")
    harvest_date = models.DateField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text="Farmer paused/listed this product")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.unit}) by {self.farmer.username}"

    @property
    def is_available(self):
        return self.stock_quantity >= self.min_order_qty and self.is_active
    
    def can_fulfill_order(self, qty):
        """Check if order quantity is valid for bulk"""
        return qty >= self.min_order_qty and qty <= self.stock_quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending - Awaiting Farmer Response'),
        ('accepted', 'Accepted - Order Confirmed'),
        ('rejected', 'Rejected - Order Cancelled'),
        ('shipped', 'Shipped - On the way'),
        ('delivered', 'Delivered - Completed'),
        ('cancelled', 'Cancelled - By Customer'),
    ]

    DELIVERY_MODE_CHOICES = [
        ('delivery', 'Home Delivery'),
        ('pickup', 'Pickup from Farm'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity ordered")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    # Delivery Details
    delivery_address = models.TextField(default='', help_text="Customer's delivery address")
    phone_number = models.CharField(max_length=15, default='', help_text="Contact number")
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODE_CHOICES, default='delivery')
    
    # Status & Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ordered_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Farmer notes
    farmer_notes = models.TextField(blank=True, help_text="Farmer's message to customer")

    def save(self, *args, **kwargs):
        # Auto-calculate total price before saving
        self.total_price = self.quantity * self.product.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} — {self.customer.username} → {self.product.name} ({self.status})"


class Cart(models.Model):
    """Shopping cart for bulk orders"""
    customer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bulk_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.customer.username}"

    def total(self):
        """Calculate total cart value"""
        return sum(item.subtotal() for item in self.items.all())

    def item_count(self):
        """Total items in cart"""
        return self.items.count()


class CartItem(models.Model):
    """Individual item in cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} in {self.cart.customer.username}'s cart"

    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.quantity * self.product.price_per_unit

    def is_valid(self):
        """Check if cart item still meets bulk requirements"""
        return (self.quantity >= self.product.min_order_qty and 
                self.quantity <= self.product.stock_quantity and 
                self.product.is_available)
