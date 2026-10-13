from shop.cart import total
from shop.catalog import product_url


def test_total():
    assert total([{'price': 10}, {'price': 5}], discount=10) == '$13.50'


def test_url():
    assert product_url('Blue  Shirt!') == '/p/blue-shirt'
