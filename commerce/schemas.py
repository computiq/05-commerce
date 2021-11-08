from typing import List

from ninja import ModelSchema, Schema
from ninja.orm import create_schema
from pydantic import UUID4

from commerce.models import Product, Merchant ,Address,City,Order,OrderStatus


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


class addressschema(ModelSchema):
    city : CitiesOut
    class Config:
        model = Address
        model_fields = [ 'id',
                         'work_address',
                         'address1',
                         'address2',
                         'phone',
                          'city',
                        ]



class addressout (UUIDSchema, addressschema):
  pass
class ADDRESSIn(Schema):
    address1: str
    address2: str
    phone : str
    work_address : bool
    city_id : UUID4 = None





class statusschema(Schema):
    is_default: bool




class statusout(UUIDSchema, statusschema):
    pass

orderscema = create_schema(Order , depth = 2 )
ordercreate = create_schema(Order , fields = ['note' , 'address' ])
