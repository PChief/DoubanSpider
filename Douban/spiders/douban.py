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
    )

    # from top to end, extract profile, photos, awards, reviews in order
    # 1st Step: extract profile info ,create file , save it
    def parse_subject(self, response):
        # parse movie root url like https://movie.douban.com/subject/1292052/
        # call parse_profile to create dir ,file, extract profile info and save them
        subject = self.parse_profile(response)
        subject.create_root_dir()
        print response.url

        ## create urls base on response.url(https://movie.douban.com/subject/1292052/), request them
        # create all_photos url , request it
        # 剧照 https://movie.douban.com/subject/1292052/photos?type=S
        stills_photos_url = response.url + 'photos?type=S'
        rqst_stills_photos = scrapy.Request(url=stills_photos_url, callback=self.parse_photos)
        # 海报 https://movie.douban.com/subject/1292052/photos?type=R
        poster_photos_url = response.url + 'photos?type=R'
        rqst_poster_photos = scrapy.Request(url=poster_photos_url, callback=self.parse_photos)
        # 壁纸 https://movie.douban.com/subject/1292052/photos?type=W
        wallpaper_photos_url = response.url + 'photos?type=W'
        rqst_wallpaper_photos = scrapy.Request(url=wallpaper_photos_url, callback=self.parse_photos)
        subject.create_photos_dir()
        rqst_stills_photos.meta['photos_dir'] = subject.photos_dir
        rqst_poster_photos.meta['photos_dir'] = subject.photos_dir
        rqst_wallpaper_photos.meta['photos_dir'] = subject.photos_dir
        # create awards url , request it
        awards_url  = response.url + 'awards'   # https://movie.douban.com/subject/1292052/awards/
        subject.create_wards_file()
        rqst_awards = scrapy.Request(url=awards_url, callback=self.parse_awards)
        rqst_awards.meta['awards_file'] = subject.awards_file
        # create reviews url , request it
        reviews_url = response.url + 'reviews'  # https://movie.douban.com/subject/1292052/reviews
        subject.create_reviews_dir_files()
        rqst_reviews = scrapy.Request(url=reviews_url, callback=self.parse_reviews)
        return rqst_stills_photos, rqst_poster_photos, rqst_wallpaper_photos, rqst_awards, rqst_reviews


    def parse_profile(self, response):
        # parse movie profile like Director,Actor ,extact name,links etc
        # extract profile data from subject page, return them
        rank_xpath = '/html/body/div[3]/div[1]/div[1]/span[1]/text()'
        rank = response.xpath(rank_xpath).extract()[0]  # No.1
        title_year = response.xpath('//*[@id="content"]/h1/span/text()').extract()
        title = title_year[0] + title_year[1] if len(title_year) == 2 else title_year[0]
        movie_name = title_year[0]
        dir_name = rank + '--' + title    #  No.1--肖申克的救赎 The Shawshank Redemption (1994)

        info = response.xpath('//*[@id="info"]').extract()[0] # id=info 页面源码

        grade_xpath = '/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/strong/text()'
        grade = response.xpath(grade_xpath).extract()[0] # u'9.6'  pass to class SetMovieFile
        # 豆瓣评分以及分布情况，页面源码部分
        grade_con = response.xpath('/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]').extract()[0]
        
        intro_xpath = '//*[@id="content"]/div[2]/div[1]/div[3]'
        intro_con = response.xpath(intro_xpath).extract()[0]
        
        subject = SetMovieFile(dir_name, movie_name, info, grade, grade_con, intro_con)
        return subject
    
    def parse_next(self, response):
        # parse next pages , just access and Rule will process
        print response.url

    # 2nd  Step: extract photos, create directory , download and save images
    def parse_photos(self, response):
        """
        1st Step: 提取当前页面的图片链接，替换为原始图片链接，发送请求，以二进制形式保存
            1st step: class="poster-col4 clearfix"  xpath='//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]'
                img_src_xpath = poster_col4.xpath + '//img/@src'
                              = '//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]//img/@src'
            访问原始图片需要登录！！！
        2nd Step: 判断是否还有下一页，若有则调用上述函数继续处理
            2nd step: class= "paginator" xpath='//*[@id="content"]/div/div[1]/div[@class="paginator"]'
                next page link xpath = pageinator.xpath + '//span[@class="next"]/@href'
                                       '//*[@id="content"]/div/div[1]/div[@class="paginator"]//span[@class="next"]/@href'
        """
        print response.url
        # 1st step
        img_src_xpath = '//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]//img/@src'
        img_src_list = response.xpath(img_src_xpath).extract()
        self.parse_img_src_list(img_src_list=img_src_list, path=response.meta['photos_dir'])
        # 2nd step
        next_page_link_xpath = '//*[@id="content"]/div/div[1]/div[@class="paginator"]//span[@class="next"]/@href'
        next_page_link = response.xpath(next_page_link_path).extract()[0]
        if next_page_link not None:
            rqst_next = scrapy.Request(url=next_page_link, callback=self.parse_photos) # 递归调用 parse_photos
            rqst_next.meta['photos_dir'] = response.meta['photos_dir']
            return rqst_next
    
    def parse_img_src_list(self, img_src_list=None, path=None):
        for img_url in img_src_list:
            # https://img3.doubanio.com/view/photo/thumb/public/p490571815.jpg
            # ====>
            # https://img3.doubanio.com/view/photo/raw/public/p490571815.jpg
            raw_img_url = img_url.replace(u'thumb', u'raw')
            rqst_raw_img = scrapy.Request(raw_img_url, callback=self.save_img)
            rqst_raw_img.meta['path'] = path
    def save_img(self, response):
        path = response.meta['path']
        img_file_name = response.url.split('/')[-1:][0]
            


    # 3rd  Step: extract awards ,  create file , save it
    def parse_awards(self, response):
        # parse awards
        content_xpath = '/html/body/div[3]/div[1]'
        content = response.xpath(content_xpath).extract()[0]
        print remove_tags(content)


    # 4th  Step: extract reviews , create file, save it
    def parse_reviews(self, response):
        # Every movie has N resviews, then N%20 + [0,1] pages
        # 后面有很多空白页，可能是为了填充页数，体现数量，在古诗文网页遇到过
        # 如：肖申克的救赎有4008个影评。但实际只到185页，共3700个影评。所以需要判断、过滤
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

# get movie name ,dir_name , subject number etc, make dir and file
class SetMovieFile():
    def __init__(self, dir_name, movie_name, info, grade, grade_con, intro_con):
        self.dir_name = dir_name
        self.movie_name = movie_name
        self.info = info
        self.grade = grade
        self.grade_con = grade_con
        self.intro_con = intro_con
        self.photos_dir = ''
        self.awards_file = ''
        self.reviews_dir = ''
        
    def create_root_dir(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name, mode=0o777)
    
    def save_info_intro_grade(self):    
        # 创建电影简介.txt， 提取内容（演职人员，剧情简介），写入文件
        intro_file_name = self.dir_name + '/' +  self.movie_name + '简介.txt'
        intro_file = open(intro_file_name, 'a')
        
        #   演职人员介绍, parse_info 
        info = remove_tags(self.info) + '\n' + '#'*99 + '\n'
        intro_file.write(info)
        #   剧情简介 parse_intro
        intro_content = remove_tags(self.intro_con)
        intro_file.write(intro_content)
        intro_file.close()
        
        ## 电影评分(9.6).txt 提取链接稍微麻烦，不是重点，暂不处理
        grade_file_name = '豆瓣评分' + '(' + str(self.grade) + ').txt'
        grade = open(grade_file_name, 'a')
        grade_content = remove_tags(self.grade_con).replace(' ', '')       # 去除多余空格
        grade_content = grade_content.replace(u'\u661f\n\n\n', u'\u661f:') # 去除多余换行，保留部分 5星:81.4%
        grade.write(grade_content)
        grade.close()
        
    # 生成图片保存目录 ./photos， 生成奖项介绍 获奖情况.txt ， 生成影评文件夹 ./影评
    def create_photos_dir(self, ):
        self.photos_dir = self.dir_name + '/' + 'photos'
        if not os.path.exists(self.photos_dir):
            os.mkdir(self.photos_dir)
    
    def create_wards_file(self, ):
        awards_file_name = self.dir_name + '/' + self.movie_name + '获奖情况.txt'
        self.awards_file = open(awards_file_name, 'a')
    
    def create_reviews_dir_files(self, ):
        self.reviews_dir = self.dir_name + '/' + 'reviews'
        if not os.path.exists(self.reviews_dir):
            os.mkdir(self.reviews_dir)
        review_list = ['一星影评.txt', '二星影评.txt', '三星影评.txt', '四星影评.txt', '五星影评.txt',]
        self.reviews = [open(self.reviews_dir + rvwls, 'a') for rvwls in review_list] # 调用的时候先判断下位置
        
process = CrawlerProcess()
process.crawl(DouBanMovie)
process.start()
