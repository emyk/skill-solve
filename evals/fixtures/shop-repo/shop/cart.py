from .utils import apply_discount, format_price, sum_prices, require_fields


def total(items, discount=0):
    return format_price(apply_discount(sum_prices(i['price'] for i in items), discount))
