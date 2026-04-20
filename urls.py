from django.urls import path
from . import views
app_name = 'farm_management'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # # Batch management
    # path('batches/', views.batch_list, name='batch_list'),
    # path('batches/create/', views.batch_create, name='batch_create'),

    # # Harvest management
    # path('harvests/', views.harvest_list, name='harvest_list'),
    # path('harvests/create/', views.harvest_create, name='harvest_create'),

    # # Sales management
    # path('sales/', views.sale_list, name='sale_list'),
    # path('sales/create/', views.sale_create, name='sale_create'),

    # # Expense management
    # path('expenses/', views.expense_list, name='expense_list'),
    # path('expenses/create/', views.expense_create, name='expense_create'),

    # # Reports
    # path('profit-loss/', views.profit_loss, name='profit_loss'),


]