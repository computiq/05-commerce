from typing import List
from django.contrib.auth.models import User

from ninja import ModelSchema, Schema
from ninja.orm import create_schema
from pydantic import UUID4
from pydantic.schema import schema

from commerce.models import City, Order, Product, Merchant


class MessageOut(Schema):
    detail: str


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
    vendor: VendorOut
    label: LabelOut
    merchant: MerchantOut
    category: CategoryOut

    class Config:
        model = Product
        model_fields = ['id',
                        'name',
                        'description',
                        'qty',
                        'price',
                        'discounted_price',
                        'vendor',
                        'category',
                        'label',
                        'merchant',

                        ]


# class ProductManualSchemaOut(Schema):
#     pass


class CitySchema(Schema):
    name: str


class CitiesOut(CitySchema, UUIDSchema):
    pass

class AddressSchema(Schema):
    work_address: bool
    address1: str
    address2: str
    phone: str


class AddressCreate(AddressSchema):
    city_id: UUID4

class AddressUpdate(AddressCreate, UUIDSchema):
    pass


class AddressOut(AddressSchema, UUIDSchema):
    city: CitiesOut

class ItemSchema(Schema):
    # user:
    product: ProductOut
    item_qty: int
    ordered: bool


class ItemCreate(Schema):
    product_id: UUID4
    item_qty: int


class ItemOut(UUIDSchema, ItemSchema):
    pass

class CheckOut(Schema):
    address_id: UUID4
    note: str
