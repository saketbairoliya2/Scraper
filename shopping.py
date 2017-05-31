# For Scrapping data from www.shopping.com
from bs4 import BeautifulSoup

import argparse
import requests
import sys
import re

SEARCH_KEY_URL = "http://www.shopping.com/products?KW={key}"
SERACH_PAGE_URL = "http://www.shopping.com/products~PG-{page_num}?KW={key}"

def print_items(items):
	'''
	Prints list in identation
	'''
    if len(items) == 0:
        print ("Nothing to show.")
        return

    for item in items:
        print ('-' * 20)
        print ('  Product : {}'.format(item.get('title', '').strip()))
        print ('  Price   : {}'.format(item.get('price', '').strip()))
        print ('  Merchant: {}'.format(
            item.get('merchant', '').strip()
        ))
    print ('-' * 20)


class ShoppingScraper(object):

	def get_listings_on_page(self, key, page_num):
		'''
		Listings are the Products with the given key and page number.
		'''
		listing_on_page = requests.get(SERACH_PAGE_URL.format(page_num=page_num, key=key))

		if listing_on_page.status_code != 200:
			raise ValueError('Searched Page/Key Not available.')

		soup = BeautifulSoup(listing_on_page.text, 'html.parser')

		return soup.select('.gridBox')


	def get_total_number_of_listing(self, key):
		'''
		For the given key it will get total listing.
		total listing = No of listing on 1st page * (no_of_page - 1) +\
		no of listings on last_page
		'''
		serach_result = requests.get(SEARCH_KEY_URL.format(key=key))
		
		if serach_result.status_code != 200:
			raise ValueError('Please Check Value of key Entered.')

		soup = BeautifulSoup(serach_result.text, 'html.parser')
		
		# Filter page_attr 'name' for all except last one - 'PLN'
		page_links = filter(
			lambda e: e.attrs.get('href') and e.attrs.get('name') != 'PLN',
			soup.select('.paginationNew a')
		)

		page_numbers = [
			self._get_page_number(each.attrs.get('href', ''))
			for each in page_links
		]

		last_page = max(page_numbers) if len(page_numbers)>0 else 0

		no_of_listing_on_first_page = len(self.get_listings_on_page(key, 1))
		no_of_listing_on_last_page = len(self.get_listings_on_page(key, last_page))

		total_listings = no_of_listing_on_first_page*(last_page-1) + \
						 no_of_listing_on_last_page

		return total_listings

	def get_product_details_from_page(self, key, page_num):
		'''
		Gets Product details inside .gridItemBtm of each element
		'''
		items = []

		for products in self.get_listings_on_page(key, page_num):
			details = products.select_one('.gridItemBtm')
			
			if details:
				product = details.select_one('.productName')
				if product:
					title = product.attrs.get('title') or\
							product.select_one('span').attrs.get('title')

				product_price = details.select_one('.productPrice')
				if product_price:
					price = product_price.string or\
							product_price.select_one('a').string

				merchant = details.select_one('.newMerchantName')
				if merchant:
					merchant_name = merchant.string or\
									merchant.select_one('a').string
				if title and price and merchant_name:
					items.append({
						'title': title, 'price': price, 'merchant': merchant_name
					})
		return items

	def _get_page_number(self, link):
		'''
		RegEx Equation to get page number from the given link 
		'''
		res = re.search(r'PG-(?P<page_num>\d+)', link)
		try:
			return int(res.group('page_num')) if res else 0
		except ValueError:
			return 0

#Program Executation starts here
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("key", help='Key to be scraped')
	parser.add_argument("page_num", default=None, nargs='?',
						help='Page number to be scraped')
	args = parser.parse_args()
	print (args.key)

	try:
		scraper = ShoppingScraper()
		print ("Total Products with key {} is {}".\
			format(args.key,scraper.get_total_number_of_listing(args.key)))

		if args.page_num:
			print_items(
				scraper.get_product_details_from_page(args.key, args.page_num)
			)

	except ValueError:
		parser.print_help()