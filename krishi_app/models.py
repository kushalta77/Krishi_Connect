from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('farmer', 'Farmer'), ('expert', 'Expert'), ('supplier', 'Supplier'), ('customer', 'Customer')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Vegetable(models.Model):
    CATEGORY_CHOICES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('grain', 'Grain'),
        ('spice', 'Spice'),
        ('other', 'Other'),
    ]
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vegetables')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='vegetable')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=[('kg', 'Kilogram'), ('ton', 'Ton'), ('quintal', 'Quintal')])
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    harvest_date = models.DateField(blank=True, null=True)
    shelf_life_days = models.PositiveIntegerField(default=7)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='vegetables/', blank=True, null=True)
    available = models.BooleanField(default=True)
    is_farmers_special = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def freshness_status(self):
        if not self.harvest_date:
            return 'unknown'
        from datetime import date
        days_old = (date.today() - self.harvest_date).days
        if days_old <= self.shelf_life_days * 0.4:
            return 'fresh'
        elif days_old <= self.shelf_life_days * 0.75:
            return 'good'
        elif days_old <= self.shelf_life_days:
            return 'aging'
        return 'expired'

    def effective_price(self):
        return self.discount_price if self.discount_price else self.price_per_unit

    def __str__(self):
        return f"{self.name} by {self.farmer.username}"

class SupplierPurchase(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_purchases')
    vegetable = models.ForeignKey(Vegetable, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed')], default='pending')
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.supplier.username} - {self.vegetable.name}"

class SupplierInventory(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    vegetable_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='supplier_inventory/', blank=True, null=True)
    available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.vegetable_name} - {self.supplier.username}"

class Cart(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    vegetable = models.ForeignKey(Vegetable, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.vegetable.price_per_unit

class CustomerOrder(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    supplier_inventory = models.ForeignKey(SupplierInventory, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('delivered', 'Delivered')], default='pending')
    ordered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.customer.username} - {self.supplier_inventory.vegetable_name}"