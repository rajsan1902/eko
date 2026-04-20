from django import forms
from .models import SpawnBatch, Harvest, Sale, Expense, Customer, Payment, Stock

class SpawnBatchForm(forms.ModelForm):
    class Meta:
        model = SpawnBatch
        fields = [
            'batch_code',
            'mushroom_type',
            'spawn_date',
            'substrate_type',
            'substrate_other',
            'status',
        ]
        widgets = {
            'spawn_date': forms.DateInput(attrs={'type': 'date'}),
            'substrate_type': forms.Select(attrs={'class': 'form-control'}),
            'substrate_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify...'}),
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

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = '__all__'
        exclude = ['final_amount']
        widgets = {
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

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
        fields = ['name', 'quantity', 'unit_price', 'supplier', 'description', 'reorder_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }