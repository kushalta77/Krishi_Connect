from django import forms
from .models import Product, Order


class ProductForm(forms.ModelForm):
    """Form for farmers to list a new product. The 'farmer' field is excluded
    and set automatically in the view from request.user."""

    class Meta:
        model = Product
        fields = ['category', 'name', 'image', 'price_per_kg', 'stock_quantity', 'harvest_date', 'description']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class OrderForm(forms.ModelForm):
    """Form for customers to place an order. Only quantity is needed;
    customer and product are set in the view."""

    class Meta:
        model = Order
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '0.1', 'step': '0.1'}),
        }

    def __init__(self, product=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if self.product and qty > self.product.stock_quantity:
            raise forms.ValidationError(
                f"Only {self.product.stock_quantity} kg available in stock."
            )
        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return qty
