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
    start_urls = [https://book.douban.com/top250?start=0']
    
    """
    通过Rule规则：
    
    1、匹配书籍介绍的链接 (https://book.douban.com/subject/1084336/)
    依次提取：
    a）书籍概况(原始图片、基本信息div[@id="info"])
    b）豆瓣评分(div.rating_wrap clearbox)
    c）内容简介(div.related_info span."all hidden" div.intro)
    d）作者简介((//div[@class="article"]//div[@class="related_info"]//div/div[@class="intro"])[2])
    e）目录(//div[@class="indent"][contains(@id,"short")] 或者  //*[@class="indent"][@style="display:none"])
    f) 书评链接，再进一步提取书评(//div[@id="reviews"]/div[@id="wt_0"]/p/a/@href)
    g) 笔记链接，再进一步提取笔记(//div[@class="ugc-mod reading-notes"]/div[@class="ft"]/p/a/@href)
    
    """
    rules = (
        # 以书目介绍链接（ttps://book.douban.com/subject/1084336/）为起点
        Rule(LinkExtractor(allow='book\.douban\.com/subject/[0-9]*/'), callback=self.parse_book_subject, follow=True, ),
        # Another 9 pages: https://book.douban.com/top250?start=50
        Rule(LinkExtractor(allow='book\.douban\.com/top250\?start=[0-9]*'), callback=self.parse_top250_rest, follow=True),
    )
    
    def parse_book_subject(self, response):
        # extract data from book link
        print response.url
        
        # 创建目录（小王子--[法]圣埃克苏佩里）前先检查目录是否存在
        book_name_xpath = '//div[@id="wrapper"]/h1/span/text()'
        author_name_xpath = '//div[@id="info"]/span[1]/a/text()'
        book_name = response.xpath(book_name_xpath).extract()[0]  # u'小王子'
        author_name = response.xpath(author_name_xpath).extract()[0]  # u'[法] 圣埃克苏佩里'
        book_dir = book_name + '--' + author_name  
        if not os.path.exists(book_dir_name):
            os.mkdir(book_dir)
        """
        保存文件目录结构
        ./小王子--[法] 圣埃克苏佩里
            小王子-[法]圣埃克苏佩里(9.0).txt
            [法]圣埃克苏佩里简介.txt
            小王子.jpg
            ./书评
                5stars--长大就笨了.txt
                ...
            ./笔记
                5stars--《小王子》的笔记-第2页.txt
                ...
        """
        book_profile_xpath = ''
        book_grade_xpath = ''
        book_intro_xpath =''
        author_intro_xpath = ''
        book_catalogue_xpath = ''
        reviews_link_xpath = ''
        annotations_link_xpath = ''
        
        
        
    def parse_top250_rest(self, response):
        # for Rule matchs next page link
        print response.url
        
    def parse_subject_annotation(self, response):
        # extract annotations from page
        print response.url  # https://book.douban.com/subject/1084336/annotation
        
        
    def parse_annotation_next(self, response):
        # for Rule matchs next pages
        print response.url
