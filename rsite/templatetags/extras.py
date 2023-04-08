from django import template

register = template.Library()

def to_sprite(pokemon_name):
    return {
        'gastrodon-east': 'gastrodon',
        'gastrodon-west': 'gastrodon',
        'urshifu-*': 'urshifu',
    }.get(pokemon_name, pokemon_name.replace(' ', '-'))

register.filter('to_sprite', to_sprite)
