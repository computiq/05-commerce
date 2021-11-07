import random
import string
from typing import List

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Product, Category, City, Vendor, Item, Address,\
    Order, OrderStatus
from commerce.schemas import ProductOut, CitiesOut, CitySchema, VendorOut,\
    ItemOut, ItemSchema, ItemCreate, CategoryOut, AddressSchema, AddressesOut,\
    AddressesCreate, AddressesUpdate, OrderSchema, OrderCreate
from config.utils.schemas import MessageOut

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])

User = get_user_model()


@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    vendor_set = Vendor.objects.all()

    if vendor_set:
        return vendor_set

    return 400, {'detail': 'No categories found'}


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
    products_set = Product.objects.filter(is_active=True).select_related('merchant', 'vendor', 'category', 'label')

    if not products_set:
        return 404, {'detail': 'No products found'}

    if q:
        products_set = products_set.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    if price_from:
        products_set = products_set.filter(discounted_price__gte=price_from)

    if price_to:
        products_set = products_set.filter(discounted_price__lte=price_to)

    if vendor:
        products_set = products_set.filter(vendor_id=vendor)

    return products_set


"""
# product = Product.objects.all().select_related('merchant', 'category', 'vendor', 'label')
    # print(product)
    #
    # order = Product.objects.all().select_related('address', 'user').prefetch_related('items')

    # try:
    #     one_product = Product.objects.get(id='8d3dd0f1-2910-457c-89e3-1b0ed6aa720a')
    # except Product.DoesNotExist:
    #     return {"detail": "Not found"}
    # print(one_product)
    #
    # shortcut_function = get_object_or_404(Product, id='8d3dd0f1-2910-457c-89e3-1b0ed6aa720a')
    # print(shortcut_function)

    # print(type(product))
    # print(product.merchant.name)
    # print(type(product.merchant))
    # print(type(product.category))


Product <- Merchant, Label, Category, Vendor

Retrieve 1000 Products form DB

products = Product.objects.all()[:1000] (select * from product limit 1000)

for p in products:
    print(p)
    
for every product, we retrieve (Merchant, Label, Category, Vendor) records

Merchant.objects.get(id=p.merchant_id) (select * from merchant where id = 'p.merchant_id')
Label.objects.get(id=p.label_id) (select * from merchant where id = 'p.label_id')
Category.objects.get(id=p.category_id) (select * from merchant where id = 'p.category_id')
Vendor.objects.get(id=p.vendor_id) (select * from merchant where id = 'p.vendor_id')

4*1000+1

Solution: Eager loading

products = (select * from product limit 1000)

mids = [p1.merchant_id, p2.merchant_id, ...]
[p1.label_id, p2.label_id, ...]
.
.
.

select * from merchant where id in (mids) * 4 for (label, category and vendor)

4+1

"""


@products_controller.get('categories', response={
    200: List[CategoryOut],
    404: MessageOut
})
def list_categories(request):
    category_set = Category.objects.all()

    if category_set:
        return category_set

    return 404, {'detail': 'No categories found'}


@address_controller.get('cities', response={
    200: List[CitiesOut],
    404: MessageOut
})
def list_cities(request):
    city_set = City.objects.all()

    if city_set:
        return city_set

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


@address_controller.get('', auth=GlobalAuth(), response={
    200: List[AddressesOut],
    404: MessageOut
})
def list_addresses(request):
    address_set = Address.objects.filter(user=request.auth['pk'])

    if address_set:
        return address_set

    return 404, {'detail': 'No addresses found'}


@address_controller.get('{id}', auth=GlobalAuth(), response={
    200: AddressesOut,
    404: MessageOut
})
def retrieve_address(request, id: UUID4):
    return get_object_or_404(Address, id=id, user=request.auth['pk'])


@address_controller.post('', auth=GlobalAuth(), response={
    201: AddressesOut,
    400: MessageOut
})
def create_address(request, address_in: AddressesCreate):
    address = Address(**address_in.dict())
    address.user = request.auth['pk']
    address.save()
    return 201, address


@address_controller.put('{id}', auth=GlobalAuth(), response={
    200: AddressesOut,
    400: MessageOut
})
def update_address(request, id: UUID4, address_in: AddressesUpdate):
    address = get_object_or_404(Address, id=id, user=request.auth['pk'])
    for attr, value in address_in.dict().items():
        setattr(address, attr, value)
    address.save()
    return 200, address


@address_controller.delete('{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_address(request, id: UUID4):
    address = get_object_or_404(Address, id=id, user=request.auth['pk'])
    address.delete()
    return 204, {'detail': ''}


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
    400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=request.auth['pk'])
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=request.auth['pk'])

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4, qty: int = 1):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= qty
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.post('item/{id}/increase-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4, qty: int = 1):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.item_qty += qty
    item.save()
    return 200, {'detail': 'Item quantity increased successfully!'}


@order_controller.delete('item/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.delete()

    return 204, {'detail': 'Item deleted!'}


@order_controller.get('', auth=GlobalAuth(), response={
    200: List[OrderSchema],
    404: MessageOut
})
def list_orders(request, ordered: bool = False):
    order_set = Order.objects.filter(user=request.auth['pk'])
    if not ordered:
        order_set = order_set.filter(ordered=ordered)
    if not order_set:
        return 404, {'detail': 'no orders found'}
    return order_set


def gen_code(size=6):
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(size))
    return code


@order_controller.post('create-order', auth=GlobalAuth(), response={
    200: MessageOut
})
def create_order(request, item_in: OrderCreate):
    user = User.objects.get(id=request.auth['pk'])
    items = Item.objects.filter(id__in=item_in.items, user=request.auth['pk'])
    current_order = Order.objects.filter(user=user, ordered=False)

    if current_order.exists():
        new_order = current_order.first()
        for i in items:
            i.ordered = True
            i.save()
        new_order.items.add(*items)
        new_order.total = new_order.order_total
        new_order.save()
        return 200, {'detail': 'updated the order successfully.'}
    else:
        for i in items:
            i.ordered = True
            i.save()
        status = OrderStatus.objects.get(title="NEW")
        new_order = Order.objects.create(
            user=user,
            status=status,
            address=item_in.address,
            ordered=False,
            ref_code=gen_code(),
            note=item_in.note
        )
        new_order.items.add(*items)
        new_order.total = new_order.order_total
        new_order.save()
        return 200, {'detail': 'created the order successfully.'}


@order_controller.post('checkout', response={
    200: MessageOut,
    404: MessageOut
})
def checkout_order(request):
    try:
        order_set = Order.objects.get(ordered=False, user=request.auth['pk'])
    except Order.DoesNotExist:
        return 404, {'detail': 'No order exists'}

    for item in order_set.items.all():
        item.product.qty -= item.item_qty
        item.product.save()
    order_set.ordered = True
    order_set.save()
    return 200, {'detail': 'checkout successful'}
