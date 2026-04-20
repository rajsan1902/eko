from django.urls import path
from . import views
urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Batch management
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),

    # Harvest management
    path('harvests/', views.harvest_list, name='harvest_list'),
    path('harvests/create/', views.harvest_create, name='harvest_create'),

    # Sales management
    path('sales/create/', views.sale_create, name='sale_create'),  # Your create view
    path('sales/', views.sale_list, name='sale_list'),  # List view (redirect after create)
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/invoice/', views.sale_invoice, name='sale_invoice'),
    path('search-customers/', views.search_customers, name='search_customers'),

    # Expense management
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),

    # Reports
    path('profit-loss/', views.profit_loss, name='profit_loss'),

    # # Stock
    path('stocks/', views.stock_list, name='stock_list'),
    path('stocks/create/', views.stock_create, name='stock_create'),
    path('stocks/<int:pk>/update/', views.stock_update, name='stock_update'),
    path('stocks/<int:pk>/delete/', views.stock_delete, name='stock_delete'),

    # Actions in batch
    path('batch/<int:pk>/edit/', views.batch_edit, name='batch_edit'),
    path('batch/<int:pk>/delete/', views.batch_delete, name='batch_delete'),

]