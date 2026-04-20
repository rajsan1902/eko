from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Stock(models.Model):
    name = models.CharField(max_length=200, help_text="Product/Item name")
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    reorder_level = models.PositiveIntegerField(default=5, help_text="Alert when stock falls below this level")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('stock_list')

    @property
    def total_value(self):
        return self.quantity * self.unit_price

    def is_low_stock(self):
        return self.quantity <= self.reorder_level

class MushroomType(models.Model):
    name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100)
    growing_days = models.IntegerField(help_text="Days from spawning to harvest")
    selling_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.variety}"

    class Meta:
        ordering = ['name']

class SpawnBatch(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('harvested', 'Harvested'),
        ('completed', 'Completed'),
    ]

    batch_code = models.CharField(max_length=50, unique=True)
    mushroom_type = models.ForeignKey(MushroomType, on_delete=models.CASCADE)
    spawn_date = models.DateField()
    substrate_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in kg")
    expected_yield = models.DecimalField(max_digits=10, decimal_places=2, help_text="Expected yield in kg")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch_code} - {self.mushroom_type.name}"

    @property
    def total_harvested(self):
        return self.harvest_set.aggregate(total=models.Sum('quantity_kg'))['total'] or 0

    @property
    def remaining_yield(self):
        return self.expected_yield - self.total_harvested

class Harvest(models.Model):
    QUALITY_CHOICES = [
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('grade_b', 'Grade B'),
    ]

    batch = models.ForeignKey(SpawnBatch, on_delete=models.CASCADE)
    harvest_date = models.DateField(default=timezone.now)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Harvest {self.batch.batch_code} - {self.harvest_date}"

    @property
    def total_value(self):
        return self.quantity_kg * self.price_per_kg

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField()
    gst_number = models.CharField(max_length=50, blank=True)
    is_wholesale = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Sale(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sale_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Sale to {self.customer.name} on {self.sale_date}"

    def save(self, *args, **kwargs):
        self.final_amount = self.total_amount - self.discount
        super().save(*args, **kwargs)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    harvest = models.ForeignKey(Harvest, on_delete=models.CASCADE)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity_kg * self.price_per_kg
        super().save(*args, **kwargs)

class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('substrate', 'Substrate Materials'),
        ('spawn', 'Spawn Purchase'),
        ('labor', 'Labor Cost'),
        ('equipment', 'Equipment'),
        ('utilities', 'Utilities'),
        ('packaging', 'Packaging'),
        ('transport', 'Transportation'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    batch = models.ForeignKey(SpawnBatch, on_delete=models.SET_NULL, null=True, blank=True)
    receipt = models.FileField(upload_to='receipts/', blank=True)

    def __str__(self):
        return f"{self.get_category_display()} - ₹{self.amount}"

class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('upi', 'UPI'),
    ])
    reference_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} for sale {self.sale.id}"