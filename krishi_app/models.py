from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('farmer', 'Farmer'), ('expert', 'Expert'), ('customer', 'Customer')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(max_length=255, blank=True, null=True)
    address2 = models.TextField(max_length=255, blank=True, null=True)
    address3 = models.TextField(max_length=255, blank=True, null=True)
    temporary_address = models.TextField(max_length=255, blank=True, null=True)
    temp_phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    official_document = models.ImageField(upload_to='documents/', blank=True, null=True)
    is_approved = models.BooleanField(default=True)  # Set to False only for farmers, others default to True
    approval_date = models.DateTimeField(blank=True, null=True)
    
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
    min_order_qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
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
    vegetable = models.ForeignKey(Vegetable, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending')
    ordered_at = models.DateTimeField(auto_now_add=True)
    viewed_by_farmer = models.BooleanField(default=False)  # Track if farmer has viewed this order
    
    def __str__(self):
        return f"{self.customer.username} - {self.vegetable.name}"


class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star - Poor'),
        (2, '2 Stars - Average'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Very Good'),
        (5, '5 Stars - Excellent'),
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.rating} stars"
    
    class Meta:
        ordering = ['-created_at']