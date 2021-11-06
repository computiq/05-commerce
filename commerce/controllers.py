from typing import List
import string
import random
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth, get_tokens_for_user
from django.contrib.auth import get_user_model, authenticate


from commerce.models import Product, Category, City, Vendor, Item, Address, Order, OrderStatus
from commerce.schemas import MessageOut, ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemSchema, ItemCreate, AddressOut, AddressCreate, OrderOut, orderstatus, checkout

User = get_user_model()


products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
city_controller = Router(tags=['cities'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])
checkout_controller = Router(tags=['checkout'])


@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    return Vendor.objects.all()

# ===================products=============================
@products_controller.get('', response={
    200: List[ProductOut],
    404: MessageOut
})
def list_products(
        request, *,
        q: str = None,
        price_from: int = None,
        price_to: int = None,
        vendor=None,
):
    products_qs = Product.objects.filter(is_active=True).select_related('merchant', 'vendor', 'category', 'label')

    if not products_qs:
        return 404, {'detail': 'No products found'}

    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    if price_from:
        products_qs = products_qs.filter(discounted_price__gte=price_from)

    if price_to:
        products_qs = products_qs.filter(discounted_price__lte=price_to)

    if vendor:
        products_qs = products_qs.filter(vendor_id=vendor)

    return products_qs


# ===================address=========================
@address_controller.get('', response=List[AddressOut])
def list_addresses(request):
    return Address.objects.all()


@address_controller.post('add-addresses', auth=GlobalAuth(), response={
    200: AddressOut
})
def create_address(request, address_in: AddressCreate):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    address = Address(**address_in.dict(), user= current_user)
    address.save()
    return 200, address


@address_controller.put('update-addresses/{id}', response={
    200: AddressOut
})
def update_address(request,id: UUID4, address_in: AddressCreate):
    address = get_object_or_404(Address, id=id)
    address.work_address = address_in.work_address
    address.address1 = address_in.address1
    address.address2 = address_in.address2
    address.city_id = address_in.city_id
    address.phone = address_in.phone
    address.save()
    return 200, address



@address_controller.delete('delete-addresses/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_address(request, id: UUID4):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    address = get_object_or_404(Address, id=id, user= current_user)
    address.delete()

    return 204, {'detail': 'Address deleted!'}


# =============city===================
@city_controller.get('cities', response={
    200: List[CitiesOut],
    404: MessageOut
})
def list_cities(request):
    cities_qs = City.objects.all()

    if cities_qs:
        return cities_qs

    return 404, {'detail': 'No cities found'}


@city_controller.get('cities/{id}', response={
    200: CitiesOut,
    404: MessageOut
})
def retrieve_city(request, id: UUID4):
    return get_object_or_404(City, id=id)


@city_controller.post('cities', response={
    201: CitiesOut,
    400: MessageOut
})
def create_city(request, city_in: CitySchema):
    city = City(**city_in.dict())
    city.save()
    return 201, city


@city_controller.put('cities/{id}', response={
    200: CitiesOut,
    400: MessageOut
})
def update_city(request, id: UUID4, city_in: CitySchema):
    city = get_object_or_404(City, id=id)
    city.name = city_in.name
    city.save()
    return 200, city


@city_controller.delete('cities/{id}',  response={
    204: MessageOut
})
def delete_city(request, id: UUID4):
    city = get_object_or_404(City, id=id)
    city.delete()
    return 204, {'detail': ''}

# ==================order==============================
@order_controller.post('create-order', auth=GlobalAuth(), response=MessageOut)
def create_order(request):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    user_items=Item.objects.filter(user=current_user,ordered=False)
    if user_items:
        order = Order.objects.create(
            user=User.objects.first(),
            status=OrderStatus.objects.get(is_default=True),
            ref_code = ''.join(random.sample(string.ascii_letters+string.digits,6)),
            ordered=False)
        user_items.update(ordered=True)
        order.items.add(*user_items)
        order.total =order.order_total
        order.save()
        return {'detail': 'order created'}
    else:
        return {'detail': 'cart is empty'}




@order_controller.get('Orders', response={
    200: List[OrderOut],
    404: MessageOut
})
def orderout(request):
    orderout = Order.objects.all()

    if orderout:
        return orderout

    return 404, {'detail': 'Not found'}


"""  
[
  {
    "NEW_id": "dcb384f7-98de-4b35-9451-22f8975218df"
  },
  {
    "REFUNDED_id": "5357bec5-4ce1-45b6-8700-2c9986fa7f2b"
  },
  {
    "COMPLETED_id": "5c8f472e-79a1-46fa-900f-3c975dd71d6c"
  },
  {
    "SHIPPED_id": "87d1f525-bf34-4469-8bd0-7437ea3915a0"
  },
  {
    "PROCESSING_id": "a1207dc4-1052-4ee9-bff7-da67397aeee4"
  }
]
"""
@checkout_controller.put('checkout', response={
    200: OrderOut
})
def checkout(request,id: UUID4, checkout_in: checkout):
    checkout = get_object_or_404(Order, id=id)
    checkout.address_id = checkout_in.address_id
    checkout.note = checkout_in.note
    checkout.ordered = True
    checkout.save()
    return 200, checkout



@order_controller.get('cart', auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    cart_items = Item.objects.filter(user=current_user, ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=current_user)
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=current_user)

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=current_user)
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}



@order_controller.post('item/{id}/increase-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=current_user)
    item.item_qty += 1
    item.save()

    return 200, {'detail': 'Item quantity increased successfully!'}


@order_controller.delete('item/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    current_user = get_object_or_404(User, id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=current_user)
    item.delete()

    return 204, {'detail': 'Item deleted!'}
