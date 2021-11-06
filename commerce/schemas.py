from typing import List

from ninja import ModelSchema, Schema
from ninja.orm import create_schema
from pydantic import UUID4

from commerce.models import Product, Merchant


class UUIDSchema(Schema):
    id: UUID4


# ProductSchemaOut = create_schema(Product, depth=2)


class VendorOut(UUIDSchema):
    name: str
    image: str


class LabelOut(UUIDSchema):
    name: str


class MerchantOut(ModelSchema):
    class Config:
        model = Merchant
        model_fields = ['id', 'name']


class CategoryOut(UUIDSchema):
    name: str
    description: str
    image: str
    children: List['CategoryOut'] = None


CategoryOut.update_forward_refs()


class ProductOut(ModelSchema):
    category: CategoryOut
    label: LabelOut
    merchant: MerchantOut
    vendor: VendorOut

    class Config:
        model = Product
        model_fields = ['id',
                        'name',
                        'description',
                        'qty',
                        'price',
                        'discounted_price',
                        'category',
                        'label',
                        'merchant',
                        'vendor',
                        ]


# class ProductManualSchemaOut(Schema):
#     pass


class CitySchema(Schema):
    name: str


class CitiesOut(CitySchema, UUIDSchema):
    pass


class AddressSchema(Schema):
    # user:
    work_address: bool = False
    address1: str
    address2: str = None
    phone: str


class AddressesCreate(AddressSchema):
    user_id: str
    city_id: UUID4


class AddressesUpdate(AddressSchema):
    city_id: UUID4


class AddressesOut(AddressSchema, UUIDSchema):
    city: CitiesOut


class ItemSchema(Schema):
    # user:
    item_qty: int
    ordered: bool
    product: ProductOut


class ItemCreate(Schema):
    product_id: UUID4
    item_qty: int


class ItemOut(ItemSchema, UUIDSchema):
    pass


class OrderStatusOut(Schema):
    title: str


class UserOut(Schema):
    username: str


class OrderSchema(Schema):
    items: List[ItemSchema]
    status: OrderStatusOut
    address: AddressesOut
    order_total: float
    ordered: bool
    user: UserOut
    ref_code: str
    note: str


class OrderCreate(Schema):
    items: List[UUID4]
    address: UUID4
    note: str
