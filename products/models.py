from django.db import models

# Create your models here.
class Collection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    featured_product = models.ForeignKey('Product', on_delete=models.SET_NULL, blank=True, null=True, related_name='+') 


    def __str__(self):
        return self.name
    

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)        
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='products')
    inventory = models.IntegerField(default=0)  
    last_updated = models.DateTimeField(auto_now=True)  
    slug = models.SlugField(default='sample-product')

    def __str__(self):
        return self.name
    

