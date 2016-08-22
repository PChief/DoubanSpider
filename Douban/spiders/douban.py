# _*_ coding:utf8 _*_

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import os
from w3lib.html import remove_tags
from scrapy.crawler import CrawlerProcess

class DouBanMovie(CrawlSpider):

    name = 'doubanmovie'
    allowed_domains = ['douban.com']
    start_urls = ['https://movie.douban.com/top250'] # all urls , commented when test single movie
    # start_urls = ['https://movie.douban.com/subject/1292052/']
    potos_url = ['/subject/[0-9]*/all_photos',
                 '/subject/[0-9]*/photos\?type=W',
                 '/subject/[0-9]*/photos\?type=R',
                 '/subject/[0-9]*/photos\?type=S']

    rules = (
        # parse  movie link, extract profile info
        Rule(LinkExtractor(allow='movie\.douban\.com/subject/[0-9]*/', deny='.*baidu.com'),
             callback='parse_subject', follow=True), # commented when test single movie

        # next page links, extract movie link for parse_subject
        Rule(LinkExtractor(allow='\?start=[0-9]*&filter=', deny='.*baidu.com', ),
             callback='parse_next', follow=True),

        # parse all_photos, extract all photos
        # Rule(LinkExtractor(allow=potos_url, deny='.*baidu.com', ),
        #      callback='parse_photos', follow=True),

        # parse awards, extract awards
        # Rule(LinkExtractor(allow='/subject/[0-9]*/awards', deny='.*baidu.com', ),
        #      callback='parse_awards', follow=True),

        # parse reviews, extract review
        # Rule(LinkExtractor(allow='movie\.douban\.com/subject/[0-9]*/reviews$', deny='.*baidu.com', ),
        #      callback='parse_reviews',),
    )

    # from top to end, extract profile, photos, awards, reviews in order
    # 1st : extract profile info ,create file , save it
    def parse_subject(self, response):
        # parse movie root url like https://movie.douban.com/subject/1292052/

        print response.url

    def parse_profile(self, response):
        # parse movie profile like Director,Actor ,extact name,links etc
        # extract profile data from subject page, return them
        rank_xpath = '/html/body/div[3]/div[1]/div[1]/span[1]/text()'
        rank = response.xpath(rank_xpath).extract()[0]  # No.1
        title_year = response.xpath('//*[@id="content"]/h1/span/text()').extract()
        title = title_year[0] + title_year[1] if len(title_year) == 2 else title_year[0]
        movie_name = title_year[0]
        dir_name = rank + '--' + title    #  No.1--肖申克的救赎 The Shawshank Redemption (1994)

        grade_xpath = '/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/strong/text()'
        grade = response.xpath(grade_xpath).extract()[0] # unicode
        grade_con = response.xpath('/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]').extract()[0]

        info = response.xpath('//*[@id="info"]').extract()[0] # id=info


    def parse_synopsis(self):
        # parse movie synopsis
        pass

    def parse_next(self, response):
        # parse next pages , just access and Rule will process
        print response.url


    # 2nd : extract photos, create directory , download and save images
    def parse_photos(self, response):
        print response.url


    # 3rd : extract awards ,  create file , save it
    def parse_awards(self, response):
        # parse awards
        content_xpath = '/html/body/div[3]/div[1]'
        content = response.xpath(content_xpath).extract()[0]
        print remove_tags(content)


    # 4th : extract reviews , create file, save it
    def parse_reviews(self, response):
        # Every movie has N resviews, then N%20 + [0,1] pages
        print response.url
        base_url = response.url + '?start='

        count_css = 'div.article div.paginator span.count::text'
        count_con = response.css(count_css).extract()[0]
        # extract int number
        count = count_con.replace(u'\u5171', '').replace(u'\u6761', '').replace('(', '').replace(')', '')
        count = int(count)
        review_pages_count = count/20
        if count%20 != 0:
            review_pages_count += 1

        page = 0
        while page <= review_pages_count:
            tail_url = str(page*20)
            url = base_url + tail_url
            yield scrapy.Request(url=url, callback=self.parse_review_start)
            page += 1


    def parse_pre_firm_review(self):
        # preprocess firm review, extact all the review urls included the next pages
        # reviews in page like https://movie.douban.com/subject/1292052/reviews
        # order by stars, 5, 4 ,,,, & get stars distribution then check if  get all
        # key: how to click show all
        review_urls = 'subjecturl' + '//reviews'
        pass

    def parse_review_start(self, response):
        print response.url


class MovieFile():
    def __init__(self, dir_name, moviename, subject,):
        self.moviename = moviename
        self.subject = subject
        self.dir_name = dir_name

    def create_dir_file(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name, mode=0o777)
        intro_file_name = self.dir_name + '/' +  self.moviename + '简介.txt'
        self.intro = open(intro_file_name, 'a', encoding='utf8')


process = CrawlerProcess()
process.crawl(DouBanMovie)
process.start()