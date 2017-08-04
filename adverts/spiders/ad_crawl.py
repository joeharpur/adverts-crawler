# -*- coding: utf-8 -*-
import scrapy, os


class AdCrawlSpider(scrapy.Spider):
	name = 'ad_crawl'
	allowed_domains = ['www.adverts.ie']#Ignore requests outside of this url
	start_urls = ['http://www.adverts.ie/']
	items_parsed = 0

	def parse(self, response):
		#extract the url for each product category and make a request to each
		category_url_list = response.css('div.holder>ul li a::attr(href)').extract()
		for url in category_url_list:
			request = scrapy.Request(url=response.urljoin(url), callback=self.parse_category)
			yield request

	def parse_category(self, response):
		#For each item, check if there are comments and extract item url
		#Make request to url, passing through num_of_comments data in request.meta field
		#Extract pagination link for next page, if it exits, and follow to end
		for div in response.css('div.search_result.info-box.quick-peek-container.bold_title_border'):
			num_of_comments = '0 comments'
			info_list = div.css('ul.date-entered li a::text').extract()
			if len(info_list) > 1:
				num_of_comments = info_list[1].strip()
			item_url = response.urljoin(div.css('div.info h4 a::attr(href)').extract_first())
			request = scrapy.Request(url=item_url, callback=self.parse_item)
			request.meta['num_of_comments'] = num_of_comments
			yield request

		next_page_url = response.css('ul.paging li.next a::attr(href)').extract_first()
		if next_page_url is not None:
			next_page_url = response.urljoin(next_page_url)
			request = scrapy.Request(url=next_page_url, callback=self.parse_category)
			yield request

	def parse_item(self, response):
		#Using css selectors, extract all pertinent information from each item
		#Not every item has the same information fields so this is filtered accordingly
		num_of_comments = response.meta['num_of_comments']
		item_name = response.css('h1.page_heading>span::text').extract_first().strip()
		item_url = response.url

		item_description = ''
		for text in response.css('div.main-description *::text').extract():
			if text not in item_description:
				item_description += text.strip()

		description_url = response.css('div.main-description a::attr(href)').extract_first()
		if description_url is not None:
			item_description += description_url

		shipping = []
		for shipping_method in response.css('div.ad-detail-box.shipping-info::text').extract()[1:]:
			shipping.append(shipping_method.strip())

		payment = []
		for payment_method in response.css('div.ad-detail-box.payment-info::text').extract()[1:]:
			payment.append(payment_method.strip())

		item_asking_price = response.css('span.ad_view_info_cell.price::text').extract_first()
		if item_asking_price is not None:
			item_asking_price = item_asking_price.strip()
		else:
			item_asking_price = response.css('span.ad_view_info_cell::text').extract_first().strip()

		seller = response.css('dd.ad_view_info_cell a::text').extract_first()
		seller_url = response.urljoin(response.css('dd.ad_view_info_cell a::attr(href)').extract_first())
		seller_positive_score = response.css('span.positive>span.count::text').extract_first()
		seller_negative_score = response.css('span.negative>span.count::text').extract_first()
		stock = 'n/a'
		phone_no = None

		info_fields = response.css('dd.ad_view_info_cell::text').extract()
		if len(info_fields) == 7:
			location = info_fields[4].strip()
			entered_or_renewed = info_fields[5].strip()
			ad_views = info_fields[6].strip()
		elif len(info_fields) == 11:
			stock = info_fields[2].strip()
			location = info_fields[8].strip()
			entered_or_renewed = info_fields[9].strip()
			ad_views = info_fields[10].strip()
		elif len(info_fields) == 8:
			phone_no = info_fields[2].strip()
			location = info_fields[5].strip()
			entered_or_renewed = info_fields[6].strip()
			ad_views = info_fields[7].strip()

		main_image_url = response.css('div.main_image img::attr(src)').extract_first()
		secondary_images = []
		for url in response.css('div#smi_gallery img::attr(src)').extract():
			secondary_images.append(url)

		breadcrumbs = []
		for trail in response.css('ul.breadcrumbs li'):
			breadcrumbs.append(trail.css('a::text').extract_first())
		breadcrumbs.remove(breadcrumbs[-1])

		#Create dictionary of information for output
		output = {'Name' : item_name,
			'URL' : item_url,
			'Description' : item_description,
			'Asking Price' : item_asking_price,
			'Location' : location,
			'Stock' : stock,
			'Seller' : seller,
			'Seller URL:' : seller_url,
			'Seller Phone No.' : phone_no,
			'Seller Feedback (positive, negative)' : (seller_positive_score, seller_negative_score),
			'Entered/Renewed' : entered_or_renewed,
			'Ad Views' : ad_views,
			'Number of Comments' : num_of_comments,
			'Breadcrumbs' : breadcrumbs,
			'Main Image' : main_image_url,
			'Secondary Images' : secondary_images}
		yield output

		#For use in terminal, displays how many items have been parsed so far
		self.items_parsed += 1
		os.system('clear')
		print('Items Parsed: ' + str(self.items_parsed))
		

		
		
