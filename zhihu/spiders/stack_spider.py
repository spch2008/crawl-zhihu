#_*_encoding:utf-8_*_
import sys
from scrapy import Spider
from scrapy import Request
from scrapy.selector import Selector
from zhihu.items import StackItem

MIN_VOTE = 1

class Item:
	
	def __init__(self, author, answer):
		self.author = author
		self.answer   = answer


class StackSpider(Spider):
	name = "zhihu"
	allowed_domains = ["zhihu.com"]
	start_urls = [
	  "http://www.zhihu.com/topic/19550517/questions",
	]
 
	def parse(self, response):
		reload(sys)
		sys.setdefaultencoding('utf-8')

		page_bar = Selector(response).xpath('//div[@class="zm-invite-pager"]/span/a/text()')
		if not page_bar:
			print "error"
			return

		page_nums	 = page_bar.extract()
		max_page_num  = int(page_nums[-2])

		for page_num in range(8000, max_page_num):
			url = response.url + "?page=" + str(page_num)
			yield Request(url, callback=self.topic_handler)
 

	def topic_handler(self, response):
			
		questions = Selector(response).xpath('//h2[@class="question-item-title"]')
		for question in questions:

			item = StackItem()

			item['title'] = question.xpath(
				'a[@class="question_link"]/text()').extract()[0]
			item['url'] = question.xpath(
				'a[@class="question_link"]/@href').extract()[0]

			url = "http://www.zhihu.com" + item['url']
			url = "http://www.zhihu.com/question/22726981"
			yield Request(url, callback=self.question_handler)

	def get_tile_detail(self, response):
 
		question_tile_ctor   = Selector(response).xpath('//h2[@class="zm-item-title zm-editable-content"]/text()')
		question_detail_ctor = Selector(response).xpath('//div[@class="zm-editable-content"]/text()')

		tiles   = question_tile_ctor.extract()
		details = question_detail_ctor.extract()

		tile   = (None if len(tiles) < 1 else tiles[0])
		detail = (None if len(details) < 1 else details[0])

		return tile, detail

	def get_question_vote_num(self, question):

		votebar = question.xpath('div[@class="zm-votebar"]/button[@class="up "]/span[@class="count"]/text()')
		if votebar == None:
		   return -1 

		count_label = votebar.extract()[0]
		if count_label.endswith('k'):
			count = float(count_label[0:-1]) * 1000
		else:
			count = int(count_label)

		return count
	

	def get_question_content(self, question):

		rich_text = question.xpath('div[@class="zm-item-rich-text"]')
		texts = rich_text.xpath('div[@class="fixed-summary zm-editable-content clearfix"]/node()').extract()
		return texts

	def get_author_descript(self, response):
		
		author_ctor   = response.xpath('div[@class="answer-head"]/div[1]/h3/a[2]/text()').extract()
		descript_ctor = response.xpath('div[@class="answer-head"]/div[1]/h3/strong/text()').extract()

		author = (None if not author_ctor else author_ctor[0])
		descript = (None if not descript_ctor else descript_ctor[0])

		if not author and not descript:
			return "匿名用户"

		if not author:
			return "知乎用户 | " + descript

		if not descript:
			return author

		return author + " | " +  descript
		

	def question_handler(self, response):

		tile, detail = self.get_tile_detail(response)
		if not tile:
			 return

		question_list = []
		questions = Selector(response).xpath('//div[@class="zm-item-answer "]')
		for question in questions:

			vote_number = self.get_question_vote_num(question)
			if vote_number < MIN_VOTE:
				continue
		   
			author = self.get_author_descript(question)
          
			texts = self.get_question_content(question) 
			if not texts:
				continue

			question_item = Item(author, texts)
			
			question_list.append(question_item)

		if len(question_list) >= 1:
		   self.record_info(tile, detail, question_list) 

	def record_info(self, tile, detail, question_list):
		text = ""
 
		text += "<h2>" + tile + "</h2>"
		text += detail;

		for question_item in question_list:
			text += "<br><br>"
			text += "<b>" + question_item.author + "</b><br>"
			text += "---------------<br>"
			for line in question_item.answer:
				text += line 
			text += "<br>"

		text += "<br><br>"
		print text
	
