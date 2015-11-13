# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
import math
import httplib
import re
import urllib2
import sys
from time import ctime
from innoshop.settings import TRY_UPDATE_TIMES
from shop.models import Product
from shop.management.commands.update_full_db import product_atributes,get_content

# atributes that we want to get
NEED_ATRIBUTES = {
    'actual_price': re.compile(u'itemprop="price">(.+)<\/span>'), 'sku':
    re.compile(u'itemprop="productID">(.+)</span>'), 'is_stock_empty':
    re.compile(
        u'<i class="icon _no"></i>(.*)')}

SETTINGS_FILE = 'shop/management/commands/settings/updater_settings.json'
LOG_FILE = 'shop/management/commands/logs/update_products_info_log_{0}.txt'.format(ctime())


class Command(BaseCommand):

    args = ''
    help = """Update existing database."""

    def handle(self, *args, **options):
        self.settings = load_settings()
        #with sys.stdout as log:
        with open(LOG_FILE,'w') as log:
            log.write(str(self.settings)+"\n")
            try:
                for num, i in enumerate(self.next_products()):
                    try:
                        new_values,code = product_atributes(
                            i.source_link,log)
                        if code == 503:
                            return
                        if code == 404:
                            Product.objects.filter(pk=i.pk).update(is_stock_empty=True)
                            log.write("pk={0} SKU={1} page not fount is_stock_empty = True \n".format(i.pk,i.SKU))
                            continue
                        try:
                            old_price = i.price
                            old_actual_price = i.actual_price
                            old_is_stock_empty = i.is_stock_empty
                            if i.SKU == new_values['SKU']:
                                product = Product.objects.filter(pk=i.pk)
                                is_stock_empty = new_values['is_stock_empty']
                                price = new_values['actual_price']
                                if i.price > 1.5*price:
                                    product.update(actual_price = price,is_stock_empty=is_stock_empty)
                                    log.write(
                                        "pk={0} SKU={1} updated actual_price ({2} -> {3}) is_stock_empty ({4} -> {5})\n".
                                        format(i.pk, i.SKU, old_actual_price,
                                            i.actual_price, old_is_stock_empty,
                                            i.is_stock_empty))
                                else:
                                    product.update(price = price,is_stock_empty=is_stock_empty)
                                    log.write(
                                        "pk={0} SKU={1} updated price ({2} -> {3}) is_stock_empty ({4} -> {5})\n".
                                        format(i.pk, i.SKU, old_price,
                                            i.price, old_is_stock_empty,
                                            i.is_stock_empty))
                            else:
                                log.write(
                                    "[ERROR] pk={0} Not the same SKU({1}) in the db and the page {2}\n".format(
                                        i.pk,
                                        i.SKU,
                                        new_values['sku']))
                        except IntegrityError:
                            log.write(
                                "[ERROR] pk={0} UNICQUE constraint failed\n".format(i.pk))
                        except IndexError:
                            i.is_stock_empty = True
                            i.save()
                            log.write(
                                "[ERROR] pk={0} SKU={1} is_stock_empty=True PARSING ERROR {3}\n". format(
                                    i.pk,
                                    i.SKU,
                                    i.source_link))
                        except KeyError:
                            log.write(
                                "[ERROR] pk={0} SKU={1} SOMETHING WRONG {2}\n". format(
                                    i.pk,
                                    i.SKU,
                                    i.source_link))
                    except (urllib2.HTTPError, urllib2.URLError) as xxx_todo_changeme:
                        httplib.IncompleteRead = xxx_todo_changeme
                        log.write(
                            "[ERROR] pk={0} SKU={1} PAGE NOT FOUND {2}\n".
                            format(i.pk, i.SKU, i.source_link))
                    except Exception as e:
                        log.write(
                            "[ERROR] pk={0} SKU={1} SOMETHING WRONG {2} {3} is_stock_empty=True\n".
                            format(i.pk, i.SKU, e,i.source_link))
                        i.is_stock_empty = True
                        i.save()
                    self.show_status(num)
            finally:
                save_settings(self.settings)
                log.close()

    def next_products(self):
        """Get list of products for checking
        CHANGE first_product"""
        first = self.settings['first_product']
        update_once = self.settings['update_once']
        last = first+update_once
        if last >= self.settings['products_in_fine']:
            last = self.settings['products_in_fine']-1
            self.settings['first_product'] = 0
        result = Product.objects.all()[first:last]
        if len(result) < update_once:
            self.settings['first_product'] = 0
        else:
            self.settings['first_product'] = first+update_once
        return result

    def show_status(self, n):
        if n == 0:
            return
        if n % 1000 == 0:
            self.stdout.write(
                '{0} updated form {1}'.format(
                    n,
                    self.settings['update_once']))
        elif n % 100 == 0:
            self.stdout.write(
                '  {0} updated from {1}'.format(
                    n,
                    self.settings['update_once']))
        elif n % 10 == 0:
            self.stdout.write(
                '     {0} updated from {1}'.format(
                    n,
                    self.settings['update_once']))


def load_settings():
    count = Product.objects.count()
    settings = {
        "try_get_times": TRY_UPDATE_TIMES,
        "first_product": 0,
        "update_once": count,
        "products_in_fine": count}
    return settings


def save_settings(settings):
    """save settings"""
    pass

def get_content(adress, try_get_times=1):
    """Getting a page with product as a string"""
    response = urllib2.urlopen(adress)
    # try to get it for some times
    for x in range(try_get_times):
        if response.getcode() == 200:
            result = response.read()
            return result
        response = urllib2.urlopen(adress)
    raise ValueError


def pars(text):
    """Parsing of the text and getting attributes values as a strings.
    RESULT is a dict.
    KEY-an attribute's name
    VALUE-an attribute's value as a string"""
    result = dict()
    for atrr in NEED_ATRIBUTES:
        regx = NEED_ATRIBUTES[atrr]
        findall = re.findall(regx, text)
        if len(findall) != 0:
            result[atrr] = findall[0]
    return result
