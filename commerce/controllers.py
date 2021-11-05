import random
import string
from typing import List

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Product, City, Vendor, Item, Order, OrderStatus, Address
from commerce.schemas import ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemCreate, OrderShemaCreat, \
    OrderOut, AdressOut, CreateAdress
from config.utils.schemas import MessageOut

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])
checkout_controller = Router(tags=['checkout'])

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

"""
finish the addresses CRUD operations
/api/addresses
"""


@address_controller.get('', auth=GlobalAuth(), response={
    200: List[AdressOut],
    404: MessageOut
})
def list_addresses(request):
    user = get_object_or_404(User, id=request.auth['pk'])
    adress_qs = Address.objects.filter(user=user).all()
    if adress_qs:
        return 200, adress_qs

    return 404, {'detail': 'No adresses found'}


@address_controller.post("add-adress", auth=GlobalAuth(), response={
    200: AdressOut
})
def add_adress(request, adress_in: CreateAdress):
    user = get_object_or_404(User, id=request.auth['pk'])
    adress = Address(**adress_in.dict(), user=user)
    adress.save()
    return 200, adress


@address_controller.delete("delete-adress{id}/", response={
    200: MessageOut
})
def delete_adress(request, adress_in: CreateAdress):
    adress = get_object_or_404(Address, id=id)
    adress.delete()
    return 200, {"dital": ""}


@address_controller.put('update-adress/{id}', auth=GlobalAuth(), response={
    200: AdressOut,
    400: MessageOut
})
def update_adress(request, id: UUID4, adress_in: CreateAdress):
    user = get_object_or_404(User, id=request.auth['pk'])
    adress = get_object_or_404(Address, id=id)
    adress.delete()
    adress = Address(id=id, **adress_in.dict(), user=user)
    adress.save()
    return 200, adress


# @products_controller.get('categories', response=List[CategoryOut])
# def list_categories(request):
#     return Category.objects.all()


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
    city = City(**city_in.dict() )
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


@order_controller.get('cart', auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    cart_items = Item.objects.filter(user=get_object_or_404(User, id=request.auth['pk']), ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    user = get_object_or_404(User, id=request.auth['pk'])
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=user, ordered=False)
        item.item_qty += 1
        item.save()
        return 200, {'detail': 'Added from cart successfully'}

    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=user)
        return 200, {'detail': 'Item Created into cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=user)
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.delete('item/{id}', response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=user)
    item.delete()

    return 204, {'detail': 'Item deleted!'}


def generate_ref_code():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


"""
'create-order' endpoint :
-    create a new order
-    set ref_code to a randomly generated 6 alphanumeric value
-    take all current items (ordered=False) and add them to the recently created order
-    set added items (ordered field) to be True
/api/orders/create
"""


@order_controller.post('create-order', auth=GlobalAuth(), response={
    200: MessageOut,
    404: MessageOut
})
def create_order(request):
    """
    * add items and mark (ordered) field as True
    * add ref_number
    * add NEW status
    * calculate the total
    """
    user = get_object_or_404(User, id=request.auth['pk'])

    orders = Order.objects.filter(user=user, ordered=False)
    user_items = Item.objects.filter(user=user).filter(ordered=False)

    for order in orders:
        order_items = Item.objects.filter(order=order.id)

    # Check If we have Precreated Order
    if user_items:
        if orders:
            for item in user_items:
                for order_item in order_items:
                    if order_item.product_id == item.product_id is not None:
                        order_item.item_qty += item.item_qty
                        order_item.save()
                        items_ = Item.objects.filter(id=item.id)
                        items_.delete()

                order.total = order.order_total
                order.save()

            # Check if we have a new items to add
            user_items = Item.objects.filter(user=user, ordered=False)
            if user_items:
                order.items.add(*user_items)
                order.total = order.order_total

                order.save()
                user_items.update(ordered=True)

            return 200, {"detail": f"Order with ID: {order.id}, Has been Updated "}

        # create New Order
        new_order = Order(user=user,
                          status=OrderStatus.objects.get(is_default=True),
                          ref_code=generate_ref_code(), ordered=False)

        new_order.save()

        new_order.items.add(*user_items)
        new_order.total = new_order.order_total

        new_order.save()
        user_items.update(ordered=True)
        return 200, {"detail": f"Order Has been Created with ID: {new_order.id}"}
    return 404, {"detail": "No Items Found"}


@order_controller.get("view-order", auth=GlobalAuth(), response={
    200: List[OrderOut],
    404: MessageOut
})
def view_order(request):
    order = Order.objects.filter(ordered=False, user=get_object_or_404(User, id=request.auth['pk']))

    if order:
        return 200, order.all()

    return 404, {"detail": "No Items Found"}


"""
checkout:
    if this user has an active order
    add address
    accept note
    update the status
    mark order.ordered field as True
"""


@checkout_controller.put("checkout", auth=GlobalAuth(), response={
    200: MessageOut,
    404: MessageOut
})
def checkout(request, order_in: OrderShemaCreat):
    user = get_object_or_404(User, id=request.auth['pk'])
    order = Order.objects.filter(user=user, ordered=False)

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
    order = Order.objects.filter(user = get_object_or_404(User, id=request.auth['pk']), ordered = True)

    if order:
        return 200, order.all()

    return 404, {"detail": "No Items Found"}
