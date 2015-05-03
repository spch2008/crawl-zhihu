#_*_encoding:utf-8_*_
import sys
import urllib2
from scrapy import Spider
from scrapy import Request
from scrapy.selector import Selector
from zhihu.items import ZhihuItem

MIN_VOTE = 0

html_fd = open("/home/spch2008/work/crawler/zhihu/zhihu/spiders/book/zhihu.html", "w")

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
			break
 

	def topic_handler(self, response):
			
		questions = Selector(response).xpath('//h2[@class="question-item-title"]')
		for question in questions:

			#item['title'] = question.xpath(
			#	'a[@class="question_link"]/text()').extract()[0]
			#item['url'] = question.xpath(
			url_last = question.xpath('a[@class="question_link"]/@href').extract()[0]

			url = "http://www.zhihu.com" + url_last
			url = "http://www.zhihu.com/question/27702564"
			yield Request(url, callback=self.question_handler)
			break

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
		if count_label.endswith('k') or count_label.endswith('K'):
			count = int(float(count_label[0:-1]) * 1000)
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

	def clear_noscript(self, line):
		
		begin   = line.find("<noscript>")
		while begin != -1:
			text  = ""
			text += line[0:begin]
			
			begin = begin + 10
			end   = line.find("</noscript>", begin)

			text += line[end+11:]

			line = text

			begin = line.find("<noscript>")

		return line

	def handle_pic(self, line):

		line = self.clear_noscript(line)

		text = ""
		pic_infos = []
			
		begin = line.find("<img")
		while begin != -1:
			prev_begin = begin 

			begin = line.find("data-ac", begin) + 16
			end   = line.find('"', begin)

			url = line[begin:end]	
			pic_name = url[url.rfind("/") + 1:]

			
			pic_info = []
			pic_info.append(url)
			pic_info.append(pic_name)
			pic_infos.append(pic_info)	

			text += line[0:prev_begin]
 

			prev_end = line.find('>', prev_begin) 

			text += '<img src="./image/' + pic_name + '"><br>'
 
			line = line[prev_end+1:]

			begin = line.find("<img")

		#last text
		text += line

		for pic_url, pic_name in pic_infos:
			file_name = "/home/spch2008/work/crawler/zhihu/zhihu/spiders/book/image/" + pic_name

			try:
				fd = open(file_name, "w")
				q  = urllib2.urlopen(pic_url)
				fd.write(q.read())
				fd.close()
				q.close()
			except:
				pass

		return text

	def record_info(self, tile, detail, question_list):
		text = ""

		if not detail:
			detail = ""
 
		text += "<h2>" + tile + "</h2>"
		text += detail;

		for question_item in question_list:
			text += "<br><br>"
			text += "<b>" + question_item.author + "</b><br>"
			text += "---------------<br>"
			for line in question_item.answer:
				if line.find("<img") != -1:
					pic_label = self.handle_pic(line)
					text += pic_label
					continue

				text += line 
			text += "<br>"

		text += "<br><br>"
   
		item = ZhihuItem()
		item['tile'] = tile
		item['question'] = detail
		item['text']     = text

		
		html_fd.write(text)

		#return item
		#print text
	
