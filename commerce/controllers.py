from typing import List
import random
import string
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from commerce.models import Product, Category, City, Vendor, Item,Order,OrderStatus,Address
from commerce.schemas import MessageOut, ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemSchema, ItemCreate,orderscema,ordercreate,addressout,ADDRESSIn
from account.authorization import GlobalAuth, get_tokens_for_user

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])

User = get_user_model()


@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    return Vendor.objects.all()


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
    products_qs = Product.objects.all().select_related('merchant', 'vendor', 'category', 'label')

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




@address_controller.get('cities', response={
    200: List[CitiesOut],
    404: MessageOut
})
def list_cities(request):
    cities_qs = City.objects.all()

    if cities_qs:
        return cities_qs

    return 404, {'detail': 'No cities found'}


@address_controller.get('cities/{id}', response={
    200: CitiesOut,
    404: MessageOut
})
def retrieve_city(request, id: UUID4):
    return get_object_or_404(City, id=id)


@address_controller.post('cities', response={
    201: CitiesOut,
    400: MessageOut
})
def create_city(request, city_in: CitySchema):
    city = City(**city_in.dict())
    city.save()
    return 201, city


@address_controller.put('cities/{id}', response={
    200: CitiesOut,
    400: MessageOut
})
def update_city(request, id: UUID4, city_in: CitySchema):
    city = get_object_or_404(City, id=id)
    city.name = city_in.name
    city.save()
    return 200, city


@address_controller.delete('cities/{id}', response={
    204: MessageOut
})
def delete_city(request, id: UUID4):
    city = get_object_or_404(City, id=id)
    city.delete()
    return 204, {'detail': ''}


@order_controller.get('cart',auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    cart_items = Item.objects.filter( user=request.auth['pk'],ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(),response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    try:
        item = Item.objects.get(product_id=item_in.product_id, user= User.objects.get(email=account_in.email))
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=request.auth['pk'])

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(),response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.post('item/{id}/increase-quantity', auth=GlobalAuth(),response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])

    item.item_qty += 1
    item.save()

    return 200, {'detail': 'Item quantity increased successfully!'}


@order_controller.delete('item/{id}', auth=GlobalAuth(),response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.delete()

    return 204, {'detail': 'Item deleted!'}





@order_controller.get('orders', auth=GlobalAuth(),response={
    200: List[orderscema],
    404: MessageOut
})
def view_orders_completed(request):
    orders = Order.objects.filter(user=request.auth['pk'],ordered=False)
    if orders:
        return orders

    return 404, {'detail': 'no completed orders yet '}


@order_controller.post('checkout', auth=GlobalAuth(),response={
    200: MessageOut,
    400 : MessageOut
})
def ckeckout(request,order__in : ordercreate):
    order = Item.objects.filter(user=request.auth['pk'], ordered=False)
    if order:
     order.update(ordered=True)
     Order.save()

     return 200, {'detail': 'create checkout successfuly'}

    else:
            return  400, {'detail': 'no orders created go and create your orders!'}

def generate_ref_code():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


@order_controller.post('create-order', auth=GlobalAuth(),response=MessageOut)
def create_order(request):


    order_qs = Order.objects.create(
        user=request.auth['pk'],
        status=OrderStatus.objects.get(is_default=True),
        ref_code=generate_ref_code(),
        ordered=False,
    )

    user_items = Item.objects.filter(user=User.objects.first()).filter(ordered=False)

    order_qs.items.add(*user_items)
    order_qs.total = order_qs.order_total
    user_items.update(ordered=True)
    order_qs.save()

    return {'detail': 'order created successfully'}


@address_controller.get('address', response={
    200: List[addressout],
    404: MessageOut
})
def list_address(request):
    address_qs = Address.objects.all().select_related('city')

    if address_qs:
        return address_qs

    return 404, {'detail': 'No addresses found'}

@address_controller.get('address/{id}', response={
    200: addressout,
    404: MessageOut
})
def retrieve_address(request, id: UUID4):
    address= get_object_or_404(Address, id=id)
    return address


@address_controller.post("/addresss" , auth=GlobalAuth())
def create_address(request, payload: ADDRESSIn):
    address = Address.objects.create(**payload.dict() , user=request.auth['pk'])
    return address



@address_controller.put("/address/{address_id}" , auth=GlobalAuth())
def update_addreses(request, address_id: UUID4, payload: ADDRESSIn):
    address = get_object_or_404(Address, id=id , user=request.auth['pk'])
    for attr, value in payload.dict().items():
        setattr(address, attr, value)
    address.save()
    return {"success": True}


@address_controller.delete("/address/{id}",auth=GlobalAuth()
    ,response = {
        204 :MessageOut
    } )
def delete_address(request, id: UUID4):
    address = get_object_or_404(Address, id=id , user=request.auth['pk'])
    address.delete()
    return 204 , {'detail' 'address deleted'}

