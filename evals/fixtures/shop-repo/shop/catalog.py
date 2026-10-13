from .utils import slugify, read_json, write_json, is_sku


def product_url(name):
    return '/p/' + slugify(name)
