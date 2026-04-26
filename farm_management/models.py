from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

class Customer(models.Model):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mobile})"

    class Meta:
        ordering = ['name']

class MushroomType(models.Model):
    name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100)
    growing_days = models.IntegerField(help_text="Days from spawning to harvest")
    selling_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.variety}"

    class Meta:
        ordering = ['name']


class Stock(models.Model):
    name = models.CharField(max_length=200, help_text="Product/Item name")
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reorder_level = models.PositiveIntegerField(default=5, help_text="Alert when stock falls below this level")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('stock_list')

    def is_low_stock(self):
        return self.quantity <= self.reorder_level


class SpawnBatch(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        
        ('incubation', 'Incubation'),
        ('fruiting', 'Fruiting'),        
        ('harvesting', 'Harvesting'),
        ('completed', 'Completed'),
    ]

    SUBSTRATE_CHOICES = [
        ('straw', 'Straw'),
        ('pellet', 'Pellet'),
        ('sawdust', 'Sawdust'),
    ]

    MUSHTYPE_CHOICES = [
        ('oyster', 'Oyster Mushroom'),
    ]

    batch_code = models.PositiveIntegerField(unique=True)
    mushroom_type = models.ForeignKey('MushroomType', on_delete=models.CASCADE)
    mushroom_type = models.CharField(max_length=20, choices=MUSHTYPE_CHOICES, default='oyster')
    batch_date = models.DateField()
    substrate_type = models.CharField(max_length=20, choices=SUBSTRATE_CHOICES, default='straw')
    number_of_bags = models.PositiveIntegerField(default=0)
    number_of_bags_contaminated = models.PositiveIntegerField(default=0)
    no_spawns_used = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch_code} - {self.mushroom_type} - {self.batch_date}"
    
    @property
    def bag_age_days(self):
        """Calculate age of the bag in days"""
        if self.batch_date:
            return (date.today() - self.batch_date).days
        return 0

    @property
    def total_harvested(self):
        return self.harvests.aggregate(total=Sum('quantity_g'))['total'] or 0

    @property
    def total_sold(self):
        return self.sale_items.aggregate(total=Sum('quantity_g'))['total'] or 0
    
    @property
    def active_bags(self):
        return self.number_of_bags-self.number_of_bags_contaminated
    


    @property
    def current_inventory(self):
        return self.total_harvested - self.total_sold

    @property
    def production_per_bag(self):
        """Calculate production per bag in grams"""
        if self.number_of_bags > 0:
            return int(self.total_harvested / self.number_of_bags)
        return 0


class Harvest(models.Model):
    batch = models.ForeignKey(
        SpawnBatch,
        on_delete=models.CASCADE,
        related_name='harvests'  # Add this
    )
    harvest_date = models.DateField(default=timezone.now)
    quantity_g = models.PositiveIntegerField(help_text="Quantity of the harvest in grams")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Harvest {self.batch.batch_code} - {self.harvest_date}"

    def save(self, *args, **kwargs):
        # Save the harvest first
        super().save(*args, **kwargs)

        # Automatically add to inventory
        MushroomInventory.objects.create(
            harvest_date=self.harvest_date,
            quantity_g=self.quantity_g,
            status='available'
        )

class MushroomInventory(models.Model):
    """Track harvested mushroom inventory in grams"""
    harvest_date = models.DateField()
    quantity_g = models.PositiveIntegerField(help_text="Quantity in grams")
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('sold', 'Sold')
    ], default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    source_harvest = models.ForeignKey(
        'Harvest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_records'
    )

    def __str__(self):
        return f"{self.harvest_date} - {self.quantity_g}g"

class Customer(models.Model):
    """Customer model to store customer information"""
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_quantity_g = models.PositiveIntegerField(default=0)
    last_purchase_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_purchases']
        indexes = [
            models.Index(fields=['mobile']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.mobile})"

    def update_purchase_stats(self):
        """Update customer purchase statistics"""
        from .models import Sale
        sales = Sale.objects.filter(customer=self)
        self.total_purchases = sales.aggregate(total=Sum('sale_amount'))['total'] or 0
        self.total_quantity_g = sales.aggregate(total=Sum('sale_quantity_g'))['total'] or 0
        self.last_purchase_date = sales.order_by('-sale_date').first().sale_date if sales.exists() else None
        self.save(update_fields=['total_purchases', 'total_quantity_g', 'last_purchase_date'])

class Sale(models.Model):
    """Simple sale record - all quantities in grams"""
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_name = models.CharField(max_length=200)  # Denormalized for quick display
    customer_mobile = models.CharField(max_length=20)  # Denormalized for quick display
    sale_date = models.DateField(default=timezone.now)
    sale_quantity_g = models.PositiveIntegerField(help_text="Quantity in grams")
    sale_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total sale amount in ₹")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name} - {self.sale_quantity_g}g - ₹{self.sale_amount}"

    @property
    def sale_quantity_kg(self):
        """Convenience property to show in kg"""
        return self.sale_quantity_g / 1000

    def save(self, *args, **kwargs):
        # Get total available harvested mushrooms in grams
        from .models import MushroomInventory
        total_available = MushroomInventory.objects.filter(
            status='available'
        ).aggregate(total=Sum('quantity_g'))['total'] or 0

        # Validate available stock
        if self.sale_quantity_g > total_available:
            raise ValueError(
                f"Insufficient harvested mushrooms! "
                f"Available: {total_available}g, "
                f"Requested: {self.sale_quantity_g}g"
            )

        # If customer is selected, update denormalized fields
        if self.customer:
            self.customer_name = self.customer.name
            self.customer_mobile = self.customer.mobile

        # Save the sale
        super().save(*args, **kwargs)

        # Update customer purchase statistics
        if self.customer:
            self.customer.update_purchase_stats()

        # Update inventory (FIFO - oldest harvest first)
        remaining_to_sell = self.sale_quantity_g
        available_stock = MushroomInventory.objects.filter(
            status='available'
        ).order_by('harvest_date')

        for stock in available_stock:
            if remaining_to_sell <= 0:
                break

            if stock.quantity_g <= remaining_to_sell:
                remaining_to_sell -= stock.quantity_g
                stock.status = 'sold'
                stock.save()
            else:
                stock.quantity_g -= remaining_to_sell
                remaining_to_sell = 0
                stock.save()

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
    stock = models.ForeignKey(Stock, on_delete=models.SET_NULL, null=True, blank=True)
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

