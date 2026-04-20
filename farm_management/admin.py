from django.contrib import admin
from .models import *

@admin.register(MushroomType)
class MushroomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'variety', 'growing_days', 'selling_price_per_kg']
    search_fields = ['name', 'variety']

@admin.register(SpawnBatch)
class SpawnBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'mushroom_type', 'status']
    list_filter = ['status', 'mushroom_type']
    search_fields = ['batch_code']
    date_hierarchy = 'batch_date'

@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = ['batch', 'harvest_date', 'quantity_g']
    list_filter = ['harvest_date']
    date_hierarchy = 'harvest_date'

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'email',]
    search_fields = ['name', 'mobile', 'email']

# @admin.register(Sale)
# class SaleAdmin(admin.ModelAdmin):
#     list_display = ['id', 'customer', 'sale_date', 'final_amount', 'payment_status']
#     list_filter = ['payment_status', 'sale_date']
#     date_hierarchy = 'sale_date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'date', 'amount', 'description']
    list_filter = ['category', 'date']
    date_hierarchy = 'date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['sale', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'payment_date']

# Register MushroomInventory
@admin.register(MushroomInventory)
class MushroomInventoryAdmin(admin.ModelAdmin):
    list_display = ['harvest_date', 'quantity_g', 'status', 'created_at']
    list_filter = ['status', 'harvest_date']
    search_fields = ['harvest_date']
    ordering = ['-harvest_date']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_mobile', 'sale_date', 'sale_quantity_g', 'sale_amount']
    list_filter = ['sale_date']
    search_fields = ['customer_name', 'customer_mobile']