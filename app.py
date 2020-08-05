import datetime
from collections import OrderedDict
import sys
import os
import csv
import re

from peewee import *
from playhouse.shortcuts import model_to_dict

db = SqliteDatabase('inventory.db')


class Product(Model):
    product_id = PrimaryKeyField()
    product_name = TextField(unique=True)
    product_quantity = IntegerField()
    product_price = IntegerField()
    date_updated = TimestampField(default=datetime.datetime.now)


    class Meta:
        database = db

def clear():
    """Clear the terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def initialize():
    db.connect()
    db.create_tables([Product], safe=True)

def take_product_input():
    product_name = input('Enter product name >>> ').strip()
    product_price = False # So user won't have to re-enter price if they get ValueError at quantity-prompt
    while True:
        try:
            if not product_price:
                product_price = int(input('Enter product price (cents) >>> '))
            product_quantity = int(input('Enter product quantity >>> '))

            return {'product_name': product_name,
                    'product_price': product_price,
                    'product_quantity': product_quantity,
                    'date_updated': datetime.datetime.now(),
                    }
        except ValueError as err:
            print(('Invalid input' + '\nError: {}').format(err))

def add_entry(product=None, verbose=True):
    """Adds a product to the database."""
    _product = take_product_input() if product == None else product
    try:
        Product.create(**_product)
    except IntegrityError:
        if Product.select().where(
            (Product.product_name == _product['product_name']) &
            (Product.date_updated <= _product['date_updated'])
        ).exists():
            Product.update({
                Product.product_price: _product['product_price'],
                Product.product_quantity: _product['product_quantity'],
                Product.date_updated: _product['date_updated'],
            }).where(
                (Product.product_name == _product['product_name']) &
                (Product.date_updated <= _product['date_updated'])
            ).execute()

            if verbose:
                print(('Product "{}" already exists. Fields updated accordingly.').format(
                    _product['product_name']
                ))
        else:
            if verbose:
                print(('A more recent version of "{}" is already stored in the database.').format(
                    _product['product_name']
                ))

def view_entries(specific=False, verbose=False):
    """Prints all the items in the database if not a specific product is passed as an argument."""
    if not specific:
        products = Product.select().order_by(Product.date_updated.desc())
    else:
        products = [specific]

    for product in products:
        if not verbose:
            print(model_to_dict(product))
        else:
            for k, v in model_to_dict(product).items():
                if k == 'product_price':
                    v = str(('${}').format(v/100))
                print(('{}: {}').format(k, v))

def view_by_id(id=None):
    """View a product (product id required)."""
    if id is None:
        while True:
            try:
                id = int(input('Enter a product id >>> '))
                product = Product.select().where(Product.product_id == id).get()
                view_entries(specific=product, verbose=True)

                break
            except (DoesNotExist, ValueError) as err:
                print(('Product not found.\nError: {}').format(err))

def export_db():
    """Exports database to csv-file."""
    pass

def dict_data_cleanup(list_of_dicts):
    """Cleans up data in line with requirements."""
    for item in list_of_dicts:
        item['product_name'] = item['product_name'].strip(),
        item['product_price'] = int(re.sub('[^0-9]', '', item['product_price']))
        item['product_quantity'] = int(item['product_quantity'])
        item['date_updated'] = datetime.datetime.strptime(item['date_updated'], '%m/%d/%Y')

    return list_of_dicts

def csv_to_dict(csv_file_name):
    """Creates a list of dictionaries from csv file."""
    with open(csv_file_name) as f:
        a = [{k: v for k, v in row.items()}
             for row in csv.DictReader(f, skipinitialspace=True, delimiter=',')]

        return dict_data_cleanup(a)

def populate_db(data):
    """Populates database with products from data. Doesn't print out exception handling."""
    with db.atomic():
        for product in data:
            add_entry(product, verbose=False)

def menu_loop():
    """Show the menu."""
    choice = None

    while choice != 'q':
        print('Enter "q" to quit.')
        for key, value in menu.items():
            print('{}) {}'.format(key, value.__doc__))
        choice = input('Action: ').lower().strip()

        if choice in menu:
            clear()
            menu[choice]()

menu = OrderedDict([
    ('a', add_entry),
    ('v', view_by_id),
    ('b', export_db),
])

if __name__ == '__main__':
    initialize()
    populate_db(csv_to_dict('inventory.csv'))
    menu_loop()
