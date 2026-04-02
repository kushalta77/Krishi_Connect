from django import forms
from .models import Product, Order


class ProductForm(forms.ModelForm):
    """Form for farmers to list a new product. The 'farmer' field is excluded
    and set automatically in the view from request.user."""

    class Meta:
        model = Product
        fields = ['category', 'name', 'image', 'price_per_unit', 'unit', 'stock_quantity', 'min_order_qty', 'harvest_date', 'description', 'is_active']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'price_per_unit': forms.NumberInput(attrs={'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'step': '0.1'}),
            'min_order_qty': forms.NumberInput(attrs={'step': '0.1'}),
        }


class OrderForm(forms.ModelForm):
    """Form for customers to place an order. Includes delivery details."""
    
    delivery_address = forms.CharField(
        label='Delivery Address',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your full delivery address'}),
        required=True
    )
    phone_number = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={'placeholder': '98xxxxxxxx'}),
        required=True
    )

    class Meta:
        model = Order
        fields = ['quantity', 'delivery_mode', 'phone_number', 'delivery_address']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '0.1', 'step': '0.1', 'placeholder': 'Enter quantity'}),
            'delivery_mode': forms.RadioSelect(),
        }

    def __init__(self, product=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if self.product:
            if not self.product.can_fulfill_order(qty):
                raise forms.ValidationError(
                    f"Order must be between {self.product.min_order_qty} and {self.product.stock_quantity} {self.product.unit}."
                )
        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return qty
