# _*_ coding:utf8 _*_

import scrapy
from scrapy.crawler import CrawlerProcess

class Click(scrapy.Spider):

    name = 'click'
    allowed_domains = ['douban.com']
    start_urls = ['https://movie.douban.com/subject/1292052/']

    def parse(self, response):
        click_dic = {'class':'bn-arrow'}
        yield scrapy.FormRequest.from_response(response=response, clickdata=click_dic, callback=self.after_click, dont_click=False)

    def after_click(self, response):
        print response.url
        con_xpath = '/html/body/div[3]/div[1]/div[2]/div[1]/div[9]/div[2]/div[1]/div[2]/div[1]/span/text()'
        content = response.xpath(con_xpath).extract()
        print u'展开全文\n'
        print content

process = CrawlerProcess()
process.crawl(Click)
process.start()