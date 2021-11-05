import random
import string
from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Address, Order, OrderStatus, Product, City, Vendor, Item, User
from commerce.schemas import AddressOut, CreateAddress, MessageOut, OrderOut, OrderSchemaCreat, ProductOut, CitiesOut, \
    CitySchema, VendorOut, ItemOut, ItemCreate

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])
checkout_controller = Router(tags=['checkout'])


# ----------------------------------------------
@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    return Vendor.objects.all()


# ----------------------------------------------
@products_controller.get('', response={
    200: List[ProductOut],
    404: MessageOut
})
def list_products(
        request, *,
        q: str = None,
        price_from: int = None,
        price_to: int = None,
        vendor=None, ):
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


# ----------------------------------------------
@address_controller.get('', auth=GlobalAuth(), response={
    200: List[AddressOut],
    404: MessageOut
})
def list_addresses(request):
    address_qs = Address.objects.filter(user=request.auth['pk']).select_related('city').all()
    if address_qs:
        return 200, address_qs

    return 404, {'detail': 'No addresses found'}


@address_controller.post("add-address", auth=GlobalAuth(), response={
    200: AddressOut
})
def add_address(request, address_in: CreateAddress):
    address = Address(**address_in.dict(), user=get_object_or_404(User, id=request.auth['pk']))
    address.save()
    return 200, address


@address_controller.delete("delete-address{id}/", auth=GlobalAuth(), response={
    200: MessageOut
})
def delete_address(request, address_in: CreateAddress):
    address = get_object_or_404(Address, id=id)
    address.delete()
    return 200, {"detail": ""}


@address_controller.put('update-address/{id}', auth=GlobalAuth(), response={
    200: AddressOut,
    400: MessageOut
})
def update_address(request, id: UUID4, address_in: CreateAddress):
    address = get_object_or_404(Address, id=id)
    address.delete()
    address = Address(id=id, **address_in.dict(), user=User.objects.first())
    address.save()
    return 200, address


@address_controller.get('cities', auth=GlobalAuth(), response={
    200: List[CitiesOut],
    401: MessageOut
})
def list_cities(request):
    cities_qs = City.objects.all()

    if cities_qs:
        return cities_qs

    return 404, {'detail': 'No cities found'}


@address_controller.get('cities/{id}', auth=GlobalAuth(), response={
    200: CitiesOut,
    404: MessageOut
})
def retrieve_city(request, id: UUID4):
    return get_object_or_404(City, id=id)


@address_controller.post('cities', auth=GlobalAuth(), response={
    201: CitiesOut,
    401: MessageOut
})
def create_city(request, city_in: CitySchema):
    user = get_object_or_404(User, id=request.auth['pk'])
    if user:
        if user.is_staff == True or user.is_superuser == True:
            city = City(**city_in.dict())
            city.save()
            return 201, city
    return 401, {'detail': 'You cant create a city'}


@address_controller.put('cities/{id}', auth=GlobalAuth(), response={
    200: CitiesOut,
    401: MessageOut
})
def update_city(request, id: UUID4, city_in: CitySchema):
    user = get_object_or_404(User, id=request.auth['pk'])
    if user:
        if user.is_staff == True or user.is_superuser == True:
            city = get_object_or_404(city_in.dict())
            city.name = city_in.name
            city.save()
            return 200, city
    return 401, {'detail': 'You cant update a city'}


@address_controller.delete('cities/{id}', auth=GlobalAuth(), response={
    204: MessageOut,
    401:MessageOut
})
def delete_city(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])
    if user:
        if user.is_staff == True or user.is_superuser == True:
            city = get_object_or_404(City, id=id)
            city.delete()
            return 204, {'detail': 'city Has been Deleted successfully'}
    return 401, {'detail': 'you cant Delete a city'}

# ----------------------------------------------

@order_controller.get('cart', auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    cart_items = Item.objects.filter(user=request.auth['pk'], ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=request.auth['pk'], ordered=False)
        item.item_qty += 1
        item.save()
        return 200, {'detail': 'Added from cart successfully'}

    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=get_object_or_404(User, id=request.auth['pk']))
        return 200, {'detail': 'Item added into cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, product_id=id, user=request.auth['pk'], ordered=False)
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}

    item.item_qty -= 1
    item.save()
    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.delete('item/{id}', auth=GlobalAuth(), response={
    200: MessageOut
})
def delete_item(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.delete()
    return 200, {'detail': 'Item deleted!'}


# ----------------------------------------------
"""
receives the item id and increase the quantity accordingly
/api/orders/item/{id}/increase-quantity
"""


@order_controller.post('item/{id}/increase-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, product_id=id, user=request.auth['pk'], ordered=False)
    if item.item_qty < 1:
        return 200, {'detail': 'Item Doesnt Exist!'}

    item.item_qty += 1
    item.save()
    return 200, {'detail': 'Item quantity increased successfully!'}


"""
'create-order' endpoint :
-    create a new order
-    set ref_code to a randomly generated 6 alphanumeric value
-    take all current items (ordered=False) and add them to the recently created order
-    set added items (ordered field) to be True
/api/orders/create
"""


def get_item_p_id(query_set):
    field_product_id = []
    for field in query_set:
        try:
            field_item = field.items.values()
            for i in field_item:
                field_product_id.append(i['product_id'])
        except:
            for item in query_set:
                field_product_id.append(item.product_id)

    return field_product_id


def generate_ref_code():
    ref_code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    return ref_code


@order_controller.post("create", auth=GlobalAuth(), response={
    200: MessageOut,
    404: MessageOut
})
def create_order(request):
    items = Item.objects.filter(user=request.auth['pk'], ordered=False)

    # Check If we have Pre-created Order
    if items:
        orders = Order.objects.filter(user=request.auth['pk'], ordered=False)
        if orders:
            for item in items:
                for order in orders:
                    order_items = Item.objects.filter(order=order.id)
                    for order_item in order_items:
                        if order_item.product_id == item.product_id is not None:
                            order_item.item_qty += item.item_qty
                            order_item.save()
                            items_ = Item.objects.filter(id=item.id)
                            items_.delete()

                order.total = order.order_total
                order.save()
            items = Item.objects.filter(user=request.auth['pk'], ordered=False)
            if items:
                order = Order.objects.get(user=request.auth['pk'], ordered=False)
                order.items.add(*items)
                order.total = order.order_total

                order.save()
                items.update(ordered=True)

            return 200, {"detail": f"Order with ID: {order.id}, Has been Ubdated "}

        # create New Order
        order = Order(user=request.auth['pk'],
                      status=OrderStatus.objects.get(is_default=True),
                      ref_code=generate_ref_code(), ordered=False)

        order.save()

        order.items.add(*items)
        order.total = order.order_total

        order.save()
        items.update(ordered=True)

        return 200, {"detail": f"Order Has been Created with ID: {order.id}"}
    return 404, {"detail": "No Items Found"}


@order_controller.get("view-order", auth=GlobalAuth(), response={
    200: List[OrderOut],
    404: MessageOut
})
def view_order(request):
    order = Order.objects.filter(user=request.auth['pk'], ordered=False)

    if order:
        return 200, order.all()

    return 404, {"detail": "No Items Found"}


@order_controller.delete("delete-order",auth=GlobalAuth(),  response={
    200: MessageOut,
    404: MessageOut
})
def delete_order(request):
    order = Order.objects.filter(user=request.auth['pk'], ordered=False)

    if Order:
        order.delete()
        return 200, {"detail": "Order Deleted"}

    return 404, {"detail": "No Items Found"}


"""
checkout:
    if this user has an active order
    add address
    accept note
    update the status
    mark order.ordered field as True
"""


@checkout_controller.put("checkout",auth=GlobalAuth(), response={
    200: MessageOut,
    404: MessageOut
})
def checkout(request, order_in: OrderSchemaCreat):
    order = Order.objects.filter(user=request.auth['pk'], ordered=False)

    if order:
        order.update(address=order_in.address_id, note=order_in.note,
                     ordered=True, status=OrderStatus.objects.get(title="PROCESSING"))

        return 200, {"detail": "Your Order Now been Processed"}

    return 404, {"detail": "No Order Found"}


@checkout_controller.get("view-processing-order", auth=GlobalAuth(), response={
    200: List[OrderOut],
    404: MessageOut
})
def view_processing_order(request):
    order = Order.objects.filter(user=request.auth['pk'], ordered=True)

    if order:
        return 200, order.all()

    return 404, {"detail": "No Items Found"}
