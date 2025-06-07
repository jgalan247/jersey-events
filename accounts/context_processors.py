from tickets.models import Cart


def cart_count(request):
    """Add cart item count to all templates"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'cart_item_count': cart.total_items}
    return {'cart_item_count': 0}