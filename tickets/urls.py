from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('cart/', views.view_cart, name='cart'),
    path('add-to-cart/<int:event_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/<uuid:order_id>/', views.payment_success, name='payment_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('ticket/<uuid:ticket_id>/qr/', views.ticket_qr_code, name='ticket_qr'),
]