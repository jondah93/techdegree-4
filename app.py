import datetime
from collections import OrderedDict
import os
import csv
import re
from decimal import Decimal

from peewee import *
from playhouse.shortcuts import model_to_dict


db = SqliteDatabase('inventory.db')


class Product(Model):
    product_id = PrimaryKeyField()
    product_name = TextField(unique=True)
    product_quantity = IntegerField(default=0)
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
                if k == 'product_price': # Print the price in dollars.
                    v = ('${}').format(Decimal(str(Decimal(v)/100)).quantize(Decimal('.00')))
                print(('{}: {}').format(k, v))

def take_product_input():
    """Takes user input and returns a dict that can be stored in db."""
    product_name = input('Enter product name >>> ').strip()
    product_price = False # So user won't have to re-enter price if they get ValueError at quantity-prompt
    while True:
        try:
            if not product_price:
                product_price = int(input('Enter product price (cents) >>> '))
            product_quantity = int(input('Enter product quantity >>> '))

            product = {'product_name': product_name,
                    'product_price': product_price,
                    'product_quantity': product_quantity,
                    'date_updated': datetime.datetime.now(),
                    }
            return product
        except ValueError as err:
            print(('Invalid input' + '\nError: {}').format(err))

def add_entry(product=None, verbose=True):
    """Add a product to the database."""
    _product = take_product_input() if product == None else product
    try:
        Product.create(**_product)
    except IntegrityError:
        try:
            Product.update({
                Product.product_price: _product['product_price'],
                Product.product_quantity: _product['product_quantity'],
                Product.date_updated: _product['date_updated'],
            }).where(
                (Product.product_name == _product['product_name']) &
                (Product.date_updated <= _product['date_updated'])
            ).execute()

            if verbose:
                print(('\nProduct "{}" already exists. Fields updated accordingly.').format(
                    _product['product_name']
                ))
        except DoesNotExist:
            if verbose:
                print(('\nA more recent version of "{}" is already stored in the database.').format(
                    _product['product_name']
                ))
        finally:
            if verbose:
                input('\nPress ENTER to continue...')

def view_by_id():
    """View a product (product id required)."""
    while True:
        clear()
        try:
            id = int(input('Enter a product id >>> '))
            product = Product.select().where(Product.product_id == id).get()
            clear()
            view_entries(specific=product, verbose=True)

            break
        except (DoesNotExist, ValueError):
            print('\nPRODUCT NOT FOUND')
        finally:
            input('\nPress ENTER to continue...')

def export_db():
    """Exports database to csv-file."""
    products = Product.select().order_by(Product.date_updated.desc())
    with open('backup.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(Product._meta.sorted_field_names)
        writer.writerows(products.tuples())

        input(('DB exported to {}.\n\nPress ENTER to continue...').format(
            (os.getcwd() + '/backup.csv')
        ))

def dict_data_cleanup(list_of_dicts):
    """Cleans up data in line with requirements."""
    for item in list_of_dicts:
        item['product_price'] = int(float(re.sub('[^0-9.]', '', item['product_price']))) * 100
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
        clear()
        for key, value in menu.items():
            print('{}) {}'.format(key, value.__doc__))
        choice = input('\nEnter an option from the menu or "q" to quit >>> ').lower().strip()
        clear()

        if choice in menu:
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
