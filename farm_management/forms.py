from django import forms
from .models import *
from django.forms import inlineformset_factory

class SpawnBatchForm(forms.ModelForm):
    class Meta:
        model = SpawnBatch
        fields = '__all__'
        exclude = ['created_by', 'created_at']
        widgets = {
            'batch_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class HarvestForm(forms.ModelForm):
    class Meta:
        model = Harvest
        fields = '__all__'
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# forms.py - Complete version

from django import forms
from .models import Sale, Customer, MushroomInventory
from django.db import models

class SaleForm(forms.ModelForm):
    # Customer selection
    customer_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or mobile...',
            'autocomplete': 'off'
        }),
        label='Search Existing Customer'
    )

    # New customer fields
    new_customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
        label='Customer Name'
    )
    new_customer_mobile = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile'}),
        label='Mobile Number'
    )

    class Meta:
        model = Sale
        fields = ['sale_date', 'sale_quantity_g', 'sale_amount']
        widgets = {
            'sale_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'sale_quantity_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity in grams',
                'min': '1',
                'step': '1'
            }),
            'sale_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total amount in ₹',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'sale_quantity_g': 'Quantity (grams)',
            'sale_amount': 'Total Amount (₹)'
        }
        help_texts = {
            'sale_quantity_g': 'Enter the quantity in grams (e.g., 500 for half kg)',
            'sale_amount': 'Total sale amount in Indian Rupees',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make date field optional (defaults to today)
        if not self.instance.pk:
            self.fields['sale_date'].initial = timezone.now().date()

    def clean_sale_quantity_g(self):
        quantity = self.cleaned_data['sale_quantity_g']

        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0 grams")

        available = MushroomInventory.objects.filter(
            status='available'
        ).aggregate(total=models.Sum('quantity_g'))['total'] or 0

        if quantity > available:
            raise forms.ValidationError(
                f"Insufficient stock! Only {available}g available. "
                f"You requested {quantity}g."
            )

        return quantity

    def clean_new_customer_mobile(self):
        mobile = self.cleaned_data.get('new_customer_mobile')
        if mobile:
            # Check if mobile already exists
            if Customer.objects.filter(mobile=mobile).exists():
                raise forms.ValidationError(
                    f"Customer with mobile {mobile} already exists. "
                    f"Please search and select from existing customers."
                )
            if len(mobile) < 10:
                raise forms.ValidationError("Mobile number must be at least 10 digits")
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        customer_search = cleaned_data.get('customer_search')
        new_customer_name = cleaned_data.get('new_customer_name')
        new_customer_mobile = cleaned_data.get('new_customer_mobile')

        # Validate that customer info is provided
        if not customer_search and not new_customer_name:
            self.add_error(None, "Please either select an existing customer or enter new customer details")

        # Validate new customer has mobile
        if new_customer_name and not new_customer_mobile:
            self.add_error('new_customer_mobile', "Mobile number is required for new customer")

        return cleaned_data


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['name', 'quantity', 'unit', 'description', 'reorder_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unit of quantity - eg: kg, nos, g, packets etc'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }