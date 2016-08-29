# _*_ coding:utf8 _*_

import scrapy
import os
from w3lib.html import remove_tags
from scrapy.crawler import CrawlerProcess
from scrapy.spiders imort CrawlSpider
from scrapy.linkextractors import LinkExtractor

# 爬取豆瓣读书top250 （https://book.douban.com/top250?icn=index-book250-all）
class DoubanBook(CrawlSpider):
    
    name = 'doubanbook'
    allowed_domains = ['douban.com', 'doubanio.com']
    start_urls = [https://book.douban.com/top250?start=25']
    
    """
    通过Rule规则：
    
    1、匹配书籍介绍的链接 (https://book.douban.com/subject/1084336/)
    提取：
    a）书籍概况
    b）豆瓣评分
    c）内容简介
    d）作者简介
    e）目录
    f) 书评链接，再进一步提取书评
    
    2、匹配读书笔记链接（https://book.douban.com/subject/1770782/annotation)
    提取:
    a) 笔记作者（头像、昵称、链接）
    b) 笔记标题
    c) 笔记内容
    d）下一页
    
    """
    rules = (
        # https://book.douban.com/subject/1084336/
        Rule(LinkExtractor(allow='book\.douban\.com/subject/[0-9]*/'), callback=self.parse_book_subject, follow=True, ),
        # Another 9 pages: https://book.douban.com/top250?start=50
        Rule(LinkExtractor(allow='book\.douban\.com/top250\?start=[0-9]*'), callback=self.parse_top250_rest, follow=True),
        
        # annotation: https://book.douban.com/subject/1770782/annotation
        Rule(LinkExtractor(allow='book\.douban\.com/subject/[0-9]*/annotation'), callback=self.parse_subject_annotation, follow=True),
        # next annotation page: '?sort=rank&start=10'
        Rule(LinkExtractor(allow='\?sort=rank&start=[0-9]*'), callback=self.parse_annotation_next, follow=True),
    
    )
    
    def parse_book_subject(self, response):
        # extract data from book link
        print response.url
        
        # 创建目录（小王子）前先检查目录是否存在，有可能subject的调用落后于annotation
        
        
    def parse_top250_rest(self, response):
        # for Rule matchs next page link
        print response.url
        
    def parse_subject_annotation(self, response):
        # extract annotations from page
        print response.url
        # 创建目录前（小王子）前先检查目录是否存在，有可能subject的调用落后于annotation
        
    def parse_annotation_next(self, response):
        # for Rule matchs next pages
        print response.url
