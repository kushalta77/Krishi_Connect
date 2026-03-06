from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('farmer', 'Farmer'), ('expert', 'Expert'), ('supplier', 'Supplier'), ('customer', 'Customer')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Vegetable(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vegetables')
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total quantity available")
    unit = models.CharField(max_length=20, choices=[('kg', 'Kilogram'), ('ton', 'Ton'), ('quintal', 'Quintal')])
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Wholesale price for suppliers")
    min_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=50, help_text="Minimum order quantity for suppliers")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='vegetables/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, help_text="Farm location")
    harvest_date = models.DateField(blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.quantity}{self.unit} by {self.farmer.username}"

class SupplierPurchase(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_purchases')
    vegetable = models.ForeignKey(Vegetable, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    delivery_address = models.TextField(blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.supplier.username} - {self.vegetable.name} ({self.quantity}{self.vegetable.unit})"

class SupplierInventory(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    vegetable_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Retail price for customers")
    min_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text="Minimum order for customers (kg)")
    image = models.ImageField(upload_to='supplier_inventory/', blank=True, null=True)
    available = models.BooleanField(default=True)
    source_purchase = models.ForeignKey(SupplierPurchase, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Supplier Inventories'
    
    def __str__(self):
        return f"{self.vegetable_name} - {self.quantity}{self.unit} by {self.supplier.username}"

class CustomerOrder(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    supplier_inventory = models.ForeignKey(SupplierInventory, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    delivery_address = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-ordered_at']
    
    def __str__(self):
        return f"{self.customer.username} - {self.supplier_inventory.vegetable_name} ({self.quantity}{self.supplier_inventory.unit})"