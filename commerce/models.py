import uuid

from PIL import Image
from django.contrib.auth import get_user_model
from django.db import models

from config.utils.models import Entity

User = get_user_model()


class Product(Entity):
    name = models.CharField(verbose_name='name', max_length=255)
    description = models.TextField('description', null=True, blank=True)
    qty = models.DecimalField('qty', max_digits=10, decimal_places=2)
    cost = models.DecimalField('cost', max_digits=10, decimal_places=2)
    img = models.ImageField('image', upload_to='products_images/',null = True)
    price = models.DecimalField('price', max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField('discounted price', max_digits=10, decimal_places=2)
    product_size = models.ManyToManyField('commerce.ProductSize',verbose_name="Size",related_name='order')
    
    category = models.ForeignKey('commerce.Category', verbose_name='category', related_name='products',
                                 null=True,
                                 blank=True,
                                 on_delete=models.SET_NULL)
    product_type = models.ForeignKey('commerce.ProductType',null=True,on_delete=models.SET_NULL,related_name="products")
    is_active = models.BooleanField('is active' , default=True)
    label = models.ForeignKey('commerce.Label', verbose_name='label', related_name='products', null=True, blank=True,
                              on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ProductType(Entity):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name


class Order(Entity):
    user = models.ForeignKey(User, verbose_name='user', related_name='orders', null=True, blank=True,
                             on_delete=models.CASCADE)
    address = models.ForeignKey('commerce.Address', verbose_name='address', null=True, blank=True,
                                on_delete=models.CASCADE)
    total = models.DecimalField('total', blank=True, null=True, max_digits=1000, decimal_places=0)
    status = models.ForeignKey('commerce.OrderStatus', verbose_name='status', related_name='orders',
                               on_delete=models.CASCADE)
    note = models.CharField('note', null=True, blank=True, max_length=255)
    ref_code = models.CharField('ref code', max_length=255)
    ordered = models.BooleanField('ordered')

    items = models.ManyToManyField('commerce.Item', verbose_name='items', related_name='order')

    def __str__(self):
        return f'{self.user.first_name} + {self.total}'

    @property
    def order_total(self):
        return sum(
            i.product.discounted_price * i.item_qty for i in self.items.all()
        )


class Item(Entity):
    """
    Product can live alone in the system, while
    Item can only live within an order
    """
    user = models.ForeignKey(User, verbose_name='user', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('commerce.Product', verbose_name='product',
                           on_delete=models.CASCADE)
    item_qty = models.IntegerField('item_qty')
    item_size = models.ForeignKey('commerce.ProductSize',null=True,on_delete=models.SET_NULL,verbose_name="Size",related_name='items')

    ordered = models.BooleanField('ordered', default=False)
    @property
    def item_total(self):
        return self.product.price * self.item_qty


    def __str__(self):
        return self.product.name



class ProductSize(Entity):
    size = models.CharField("Size",max_length=20)
    def __str__(self):
        return self.size


class OrderStatus(Entity):
    NEW = 'NEW'  # Order with reference created, items are in the basket.
    # CREATED = 'CREATED'  # Created with items and pending payment.
    # HOLD = 'HOLD'  # Stock reduced but still awaiting payment.
    # FAILED = 'FAILED'  # Payment failed, retry is available.
    # CANCELLED = 'CANCELLED'  # Cancelled by seller, stock increased.
    PROCESSING = 'PROCESSING'  # Payment confirmed, processing order.
    SHIPPED = 'SHIPPED'  # Shipped to customer.
    COMPLETED = 'COMPLETED'  # Completed and received by customer.
    REFUNDED = 'REFUNDED'  # Fully refunded by seller.

    title = models.CharField('title', max_length=255, choices=[
        (NEW, NEW),
        (PROCESSING, PROCESSING),
        (SHIPPED, SHIPPED),
        (COMPLETED, COMPLETED),
        (REFUNDED, REFUNDED),
    ])
    is_default = models.BooleanField('is default')

    def __str__(self):
        return self.title


class Category(Entity):
    types = models.ManyToManyField('commerce.ProductType',verbose_name='Types',related_name='categories',null=True,blank=True)
    name = models.CharField('name', max_length=255)
    description = models.TextField('description')
    image = models.ImageField('image', upload_to='category/')
    is_active = models.BooleanField('is active',default=True)


    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    @property
    def children(self):
        return self.children

class Merchant(Entity):
    name = models.CharField('name', max_length=255)

    def __str__(self):
        return self.name


class ProductImage(Entity):
    image = models.ImageField('image', upload_to='product/')
    is_default_image = models.BooleanField('is default image')
    product = models.ForeignKey('commerce.Product', verbose_name='product', related_name='images',
                                on_delete=models.CASCADE)

    def __str__(self):
        return str(self.product.name)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)
        if img.height > 500 or img.width > 500:
            output_size = (500, 500)
            img.thumbnail(output_size)
            img.save(self.image.path)
            # print(self.image.path)


class Label(Entity):
    name = models.CharField('name', max_length=255)

    class Meta:
        verbose_name = 'label'
        verbose_name_plural = 'labels'

    def __str__(self):
        return self.name


class Vendor(Entity):
    name = models.CharField('name', max_length=255)
    image = models.ImageField('image', upload_to='vendor/')

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)
        if img.height > 500 or img.width > 500:
            output_size = (500, 500)
            img.thumbnail(output_size)
            img.save(self.image.path)
            # print(self.image.path)


class City(Entity):
    name = models.CharField('city', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'city'
        verbose_name_plural = 'cities'


class Address(Entity):
    user = models.ForeignKey(User, verbose_name='user', related_name='address',
                             on_delete=models.CASCADE)
    work_address = models.BooleanField('work address', null=True, blank=True)
    address1 = models.CharField('address1', max_length=255)
    address2 = models.CharField('address2', null=True, blank=True, max_length=500)
    city = models.CharField('city', null=True, blank=True, max_length=100)
    phone = models.CharField('phone', max_length=255)

    def __str__(self):
        return f'{self.user.first_name} - {self.address1} - {self.address2} - {self.phone}'


""" class Address2(Entity):
    user = models.ForeignKey(User, verbose_name='user', related_name='address',
                             on_delete=models.CASCADE)
    work_address = models.BooleanField('work address', null=True, blank=True)
    address1 = models.CharField('address1', max_length=255)
    address2 = models.CharField('address2', null=True, blank=True, max_length=255)
    city = models.ForeignKey(City, related_name='addresses', on_delete=models.CASCADE)
    phone = models.CharField('phone', max_length=255)

    def __str__(self):
        return f'{self.user.first_name} - {self.address1} - {self.address2} - {self.phone}' """