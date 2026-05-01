from django import template

register = template.Library()

@register.simple_tag
def calculate_total(products, quantities):
    total = 0

    for product in products:
        qty = quantities.get(str(product.id), 0)

        price = product.discount_price if product.discount_price else product.price
        total += price * qty

    return total