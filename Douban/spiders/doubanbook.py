# _*_ coding:utf8 _*_

import scrapy
import os
from w3lib.html import remove_tags
from scrapy.crawler import CrawlerProcess
from scrapy.spiders imort CrawlSpider
from scrapy.linkextractors import LinkExtractor

# 爬取豆瓣读书top250 （https://book.douban.com/top250?icn=index-book250-all）
class DouBanBook(CrawlSpider):
    
    name = 'doubanbook'
    allowed_domains = ['douban.com', 'doubanio.com']
    start_urls = [https://book.douban.com/top250?start=0']
    
    """
    通过Rule规则：
    
    1、匹配书籍介绍的链接 (https://book.douban.com/subject/1084336/)
    依次提取：
    a）书籍概况(原始图片、基本信息div[@id="info"])
    b）豆瓣评分(//div[@class="rating_wrap clearbox"])
    c）内容简介(//span[@class="all hidden"]//div[@class="intro"])
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
        # step 1: extract data from book link
        print response.url
        
        # step 1.1 : 创建目录（小王子--[法]圣埃克苏佩里）
        book_name_xpath = '//div[@id="wrapper"]/h1/span/text()'
        author_name_xpath = '//div[@id="info"]/span[1]/a/text()'
        book_name = response.xpath(book_name_xpath).extract()[0]  # u'小王子'
        author_name = response.xpath(author_name_xpath).extract()[0]  # u'[法] 圣埃克苏佩里'
        book_dir = book_name + '--' + author_name  
        if not os.path.exists(book_dir_name):
            os.mkdir(book_dir)
        self.save_subject_profile(response=response, book_dir=book_dir, book_name=book_name, author_name=author_name)
        
        # step 1.4 : extract reviews_link and annotations_link, yield them
        reviews_link_xpath = '//div[@id="reviews"]/div[@id="wt_0"]/p/a/@href'
        reviews_link = response.xpath(reviews_link_xpath).extract()[0]
        # https://book.douban.com/subject/1084336/reviews
        reviews_dir = book_dir + '/' + 'reviews'
        if not os.path.exists(reviews_dir):
            os.mkdir(reviews_dir)
        rqst_reviews_link = Request(url=reviews_link, callback=self.parse_rvws_ants)
        rqst_reviews_link.meta['path'] = reviews_dir
        rqst_reviews_link.meta['xpath_urls'] = '//*[@class="review-list"]//div/header/h3/a/@href'
        rqst_reviews_link.meta['xpath_next_page'] = '//span[@class="next"]/link/@href'
        rqst_reviews_link.meta['callback'] =self.parse_review
        yield rqst_reviews_link
        
        annotations_link_xpath = '//div[@class="ugc-mod reading-notes"]/div[@class="ft"]/p/a/@href'
        annotations_link = response.xpath(annotations_link_xpath).extract()[0]
        # https://book.douban.com/subject/1084336/annotation
        annotations_dir = book_dir + '/' + 'annotations'
        if not os.path.exists(annotations):
            os.mkdir(annotations_dir)
        rqst_annotations_link = Request(url=annotations_link, callback=self.parse_annotations)
        rqst_reviews_link.meta['annotations_dir'] = annotations_dir
        yield rqst_annotations_link
        
    def save_subject_profile(self, response, book_dir, book_name, author_name):
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
        book_profile_xpath = 'div[@id="info"]'
        book_grade_xpath = '//div[@class="rating_wrap clearbox"]'
        book_intro_xpath = '//span[@class="all hidden"]//div[@class="intro"]'
        # 目录的xpath需要判断
        book_catalogue_short_xpath = '//div[@class="indent"][contains(@id,"short")]'
        book_catalogue_display_xpath = '//*[@class="indent"][@style="display:none"]'
        author_intro_xpath = '//div[@class="article"]//div[@class="related_info"]//div/div[@class="intro"])[2]'
        
        # step 1.2 : extract book_profile , book_grade, book_intro, book_catalogue, save them
        book_profile = response.xpath(book_profile_xpath).extract()[0]
        book_grade = response.xpath().extract(book_grade_xpath)[0]
        book_grade = remve_tags(book_grade)
        book_grade_mark = ''  # (9.0)
        book_intro = response.xpath(book_intro_xpath).extract()[0]
        book_intro = remove_tags(book_intro)
        book_catalogue = response.xpath(book_catalogue_xpath).extract()[0]
        book_catalogue = remove_tags(book_catalogue)
        
        book_file_name = book_dir + '/' + book_dir + book_grade_mark + '.txt'
        book_file = open(book_file_name, 'a')
        book_file.write(
            book_name + '\n\n' +
            book_profile + '\n\n' +
            book_grade + '\n\n' +
            book_intro + '\n\n' +
            book_catalogue + '\n\n'
            )
        book_file.close()
        
        # step 1.3 : extract author intro, save it
        author_intro_file_name = book_dir + '/' + author_name + u'简介.txt'
        author_intro_file = open(author_intro_file_name, 'a')
        author_intro = response.xpath(author_intro_xpath).extract()[0]
        author_intro = remove_tags(author_intro)
        author_intro_file.write(
            author_name + u'简介' + '\n\n' +
            author_intro
            )
        author_intro_file.close()
    
    def parse_rvws_ants(self, response):
        """
        参数说明
        path: 保存书评文件、笔记文件的目录
        xpath_urls: 用于提取页面中review或者annotation的URL列表
        xpath_next_page: 用于提取下一页的链接后缀，需要加上base_url才能访问
        callback: 请求单个review或者annotation页面的回调函数
        """
        print response.url
        rvws_uants_url_list_xpath = response.meta['xpath_urls']
        rvws_uants_url_list = response.xpath(rvws_uants_url_list_xpath).extract()
        for rvw_uant_url in rvws_uants_url_list:
            rqst = Request(url=rvw_uant_url, callback=response.meta['callback'])
                rqst.meta['path'] = response.meta['path']
                yield rqst
        
        # parse next reviews page
        base_url = response.url.split('?')[0]
        next_page_url_xpath = response.meta['xpath_next_page']
        next_page_url = response.xpath(next_page_url_xpath).extract()
        if next_page_url:
            next_page_url = base_url + next_page_url[0]
            # 递归调用自身
            rqst_next_page = Request(url=next_page_url, callback=self.parse_rvws_ants)
            rqst_next_page.meta['path'] = response.meta['path']
            rqst_next_page.meta['xpath_urls'] = response.meta['xpath_urls']
            rqst_next_page.meta['xpath_next_page'] = response.meta['xpath_next_page']
            rqst_next_page.meta['callback'] = response.meta['callback']
            yield rqst_next_page
    
    def parse_annotations(self, response):
        print response.url
        path = response.meta['annotations_dir']
    
        
    def parse_review(self, response):
        print response.url
    
    def parse_annotation(self, response):
        print response.url
        
    def parse_top250_rest(self, response):
        # for Rule matchs next page link
        print response.url
        
    def parse_subject_annotation(self, response):
        # extract annotations from page
        print response.url  # https://book.douban.com/subject/1084336/annotation
        
        
    def parse_annotation_next(self, response):
        # for Rule matchs next pages
        print response.url


process = CrawlerProcess()
process.crawl(DouBanBook)
process.start()
