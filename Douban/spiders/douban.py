# _*_ coding:utf8 _*_

import scrapy
import os
from w3lib.html import remove_tags
from scrapy.crawler import CrawlerProcess


class DouBanMovie(scrapy.Spider):

    name = 'doubanmovie'
    allowed_domains = ['douban.com', 'doubanio.com']

    def start_requests(self):
        # start_requests 不能与Rule规则同时使用
        return [scrapy.FormRequest('https://www.douban.com/accounts/login',
                                   formdata={'form_email': 'email', 'form_password': 'password'},
                                   callback=self.loged_in)]

    def loged_in(self, response):
        # 爬取所有250部电影相关信息
        start_url = 'https://movie.douban.com/top250'
        return scrapy.Request(url=start_url, callback=self.parse_start_url)
        # 测试代码时只使用一个电影链接
        # start_url = 'https://movie.douban.com/subject/1292052/'
        # return scrapy.Request(url=start_url, callback=self.parse_subject)

    def parse_start_url(self, response):
        # 提取出所有电影链接（https://movie.douban.com/subject/1292052/）
        movie_urls = response.xpath('//*[@id="content"]//*[@class="hd"]/a/@href').extract()
        for movie_url in movie_urls:
            yield scrapy.Request(url=movie_url, callback=self.parse_subject)

        next_page_link_xpath = '//span[@class="next"]/a/@href'
        next_page_link = response.xpath(next_page_link_xpath).extract()[0]
        next_page_link = response.url + next_page_link
        if next_page_link:
            yield scrapy.Request(url=next_page_link, callback=self.parse_start_url)  # 递归调用 parse_start_url

    # 在页面由上至下，依次提取概况、评分信息、简介、图片、获奖情况、影评等信息
    # 1st Step: extract profile info ,create file , save it
    def parse_subject(self, response):
        # parse movie root url like https://movie.douban.com/subject/1292052/
        # 调用 parse_profile 提取概况信息、评分信息以及简介，并保存
        subject = self.parse_profile(response)
        subject.create_root_dir()
        subject.save_info_intro_grade()
        #print response.url

        # 基于response.url(https://movie.douban.com/subject/1292052/)生成图片、获奖情况、影评等链接,发送请求
        # 生成三种图片链接：剧照、海报、壁纸，传入图片保存目录
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
        # 生成获奖情况链接，传入获奖情况文件
        awards_url = response.url + 'awards'   # https://movie.douban.com/subject/1292052/awards/
        subject.create_wards_file()
        rqst_awards = scrapy.Request(url=awards_url, callback=self.parse_awards)
        rqst_awards.meta['awards_file'] = subject.awards_file
        # 生成影评链接，传入一至五星影评文件目录
        reviews_url = response.url + 'reviews'  # https://movie.douban.com/subject/1292052/reviews
        subject.create_reviews_dir_files()
        rqst_reviews = scrapy.Request(url=reviews_url, callback=self.parse_reviews)
        rqst_reviews.meta['reviews_dirs'] = subject.reviews_dirs
        return rqst_stills_photos, rqst_poster_photos, rqst_wallpaper_photos, rqst_awards, rqst_reviews

    def parse_profile(self, response):
        # parse movie profile like Director,Actor ,extact name,links etc
        # extract profile data from subject page, return them
        rank_xpath = '/html/body/div[3]/div[1]/div[1]/span[1]/text()'
        rank = response.xpath(rank_xpath).extract()[0]  # No.1
        title_year = response.xpath('//*[@id="content"]/h1/span/text()').extract()
        title = title_year[0] + title_year[1] if len(title_year) == 2 else title_year[0]
        movie_name = title_year[0]
        dir_name = rank + '--' + title    # No.1--肖申克的救赎 The Shawshank Redemption (1994)
        dir_name = self.clean_invilad_chracter(dir_name)

        info = response.xpath('//*[@id="info"]').extract()[0] # id=info 页面源码

        grade_xpath = '/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/strong/text()'
        grade = response.xpath(grade_xpath).extract()[0]  # u'9.6'  pass to class SetMovieFile
        # 豆瓣评分以及分布情况，页面源码部分
        grade_con = response.xpath('/html/body/div[3]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]').extract()[0]
        
        intro_xpath = '//*[@id="link-report"]/span[@class="all hidden"]/text()'
        intro_content = response.xpath(intro_xpath).extract()  #有的简介比较长，处于隐藏状态
        intro_con = ''
        if intro_content:
            for intro_co in intro_content:
                intro_con = intro_con + intro_co
        else:
            intro_xpath = '//*[@id="content"]/div[2]/div[1]/div[3]'
            intro_con = response.xpath(intro_xpath).extract()[0]
        subject = SetMovieFile(dir_name, movie_name, info, grade, grade_con, intro_con)
        return subject


    # 2nd  Step: extract photos, create directory , download and save images
    def parse_photos(self, response):
        """
        1st Step: 提取当前页面的图片链接，替换为原始图片链接，发送请求，以二进制形式保存
            class="poster-col4 clearfix"  xpath='//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]'
                img_src_xpath = poster_col4.xpath + '//img/@src'
                              = '//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]//img/@src'
            访问原始图片需要登录！！！
        2nd Step: 判断是否还有下一页，若有则调用上述函数继续处理
            class= "paginator" xpath='//*[@id="content"]/div/div[1]/div[@class="paginator"]'
                next page link xpath = pageinator.xpath + '//span[@class="next"]/@href'
                            '//*[@id="content"]/div/div[1]/div[@class="paginator"]//span[@class="next"]/@href'
        """
        print response.url
        # 1st step
        img_src_xpath = '//*[@id="content"]/div/div[1]/ul[@class="poster-col4 clearfix"]//img/@src'
        img_src_list = response.xpath(img_src_xpath).extract()
        path = response.meta['photos_dir']
        for img_url in img_src_list:
            # https://img3.doubanio.com/view/photo/thumb/public/p490571815.jpg
            # ====>
            # https://img3.doubanio.com/view/photo/raw/public/p490571815.jpg
            raw_img_url = img_url.replace(u'thumb', u'raw')
            print 'raw_img_url:::::', raw_img_url
            rqst_raw_img = scrapy.Request(raw_img_url, callback=self.save_img)
            rqst_raw_img.meta['path'] = path
            yield rqst_raw_img

        # 2nd step
        next_page_link_xpath = '//span[@class="next"]/a/@href'
        next_page_link = response.xpath(next_page_link_xpath).extract()
        if next_page_link:
            # 递归调用 parse_photos，处理下一页中的photos链接
            rqst_next = scrapy.Request(url=next_page_link[0], callback=self.parse_photos)  
            print 'Next img page link :', next_page_link[0]
            rqst_next.meta['photos_dir'] = response.meta['photos_dir']
            yield rqst_next

    def save_img(self, response):
        path = response.meta['path']
        img_file_name = path + '/' + response.url.split('/')[-1]
        img_file = open(img_file_name, 'wb')
        img_file.write(response.body)
        img_file.close()


    # 3rd  Step: extract awards ,  create file , save it
    def parse_awards(self, response):
        content_xpath = '/html/body/div[3]/div[1]'
        content = response.xpath(content_xpath).extract()[0]
        content = remove_tags(content)
        awards_file = response.meta['awards_file']
        awards_file.write(content.encode('utf8'))
        awards_file.close()


    # 4th  Step: extract reviews , create file, save it
    def parse_reviews(self, response):
        # 每个电影共有N条影评,则有 N%20 + [0,1] 页影评
        # 有些页面会折叠评论，但链接仍然在
        # print response.url
        base_url = response.url + '?start='

        count_css = 'div.article div.paginator span.count::text'
        count_con = response.css(count_css).extract()[0]  # u'(\u51713995\u6761)' in 肖申克的救赎的影评
        # 提取出影评个数，如 3995 （in 肖申克的救赎 The Shawshank Redemption）
        count = count_con.replace(u'\u5171', '').replace(u'\u6761', '').replace('(', '').replace(')', '')
        count = int(count)  # for example 3995
        review_pages_count = count/20
        if count % 20 != 0:
            review_pages_count += 1
        page = 0  # start with https://movie.douban.com/subject/1292052/reviews?start=0
        while page <= review_pages_count:
            tail_url = str(page*20)
            url = base_url + tail_url
            # https://movie.douban.com/subject/1292052/reviews?start=0
            rqst_url = scrapy.Request(url=url, callback=self.parse_review_start)
            rqst_url.meta['reviews_dirs'] = response.meta['reviews_dirs']
            yield rqst_url
            page += 1

    def parse_review_start(self, response):
        print response.url
        # extract review url , request it, check if exists
        reviews_urls = response.xpath('//header/h3/a/@href').extract()
        if reviews_urls:
            for review_url in reviews_urls:
                # https://movie.douban.com/review/1000369/
                rqst_review = scrapy.Request(url=review_url, callback=self.parse_review)
                rqst_review.meta['reviews_dirs'] = response.meta['reviews_dirs']
                yield rqst_review

    def parse_review(self, response):
        reviews_dirs = response.meta['reviews_dirs']  # ['一星影评', '二星影评',,,]
        stars_class_xpath = '//div[@class="article"]//header//span[contains(@class,"allstar")]/@class'
        if response.xpath(stars_class_xpath).extract()[0]:
            stars_class = response.xpath(stars_class_xpath).extract()[0]
            allstars = stars_class.split()[0]  # u'allstar50'
            stars_num = int(allstars[-2:-1]) - 1 # 5-1  --> 4
        else:
            stars_num = 1  #如果评论中没有打星，则按照1星计算
        review_file_dir = reviews_dirs[stars_num]
        review_title_xpath = '//*[@id="content"]/h1//span/text()'
        review_title = response.xpath(review_title_xpath).extract()[0].replace('"', '')
        review_title = self.clean_invilad_chracter(review_title)  #清除非法字符串
        review_file_full_path = review_file_dir + '/' + review_title + '.txt'
        review_file = open(review_file_full_path, 'a')
        author_nickname_xpath = '//div[@class="article"]//header/a/span/text()'
        author_nickname = response.xpath(author_nickname_xpath).extract()[0]
        author_icon_img_src_xpath = '//div[@class="article"]//div[@class="main"]/a/img/@src'
        #  u'https://img3.doubanio.com/icon/u1000152-14.jpg'
        author_icon_img_src = response.xpath(author_icon_img_src_xpath).extract()[0]
        author_link_xpath = '//div[@class="article"]//header/a[1]/@href'
        author_link = response.xpath(author_link_xpath).extract()[0]
        review_content_xpath = '//*[@id="link-report"]/div'
        review_content = response.xpath(review_content_xpath).extract()[0]
        review_content = remove_tags(review_content)
        review_file.write(review_title.encode('utf8') + '\n')
        review_file.write('影评链接:' + response.url + '\n')
        review_file.write('作者昵称：' + author_nickname.encode('utf8') + '\n')
        review_file.write('作者链接：' + author_link.encode('utf8') + '\n\n\n')
        review_file.write(review_content.encode('utf8'))
        review_file.close()
        author_icon_img_name = author_icon_img_src.split('/')[-1]
        author_icon_img_file = open(review_file_dir + '/' + author_icon_img_name, 'wb')
        rqst_author_icon = scrapy.Request(url=author_icon_img_src, callback=self.save_author_icon)
        rqst_author_icon.meta['author_icon_img_file'] = author_icon_img_file
        yield rqst_author_icon

    def clean_invilad_chracter(self, strings):
        # 剔除非法字符
        invalid_chr = r'\/:*?"<>|'
        for chr in invalid_chr:
            strings = strings.replace(chr, '')
        return strings

    def save_author_icon(self, response):
        author_icon_img_file = response.meta['author_icon_img_file']
        author_icon_img_file.write(response.body)
        author_icon_img_file.close()


# 获取电影名称等信息用于创建目录、文件
class SetMovieFile:
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
        self.reviews_dirs = []
        
    def create_root_dir(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name)  # add arguments mode=0o777 on linux
    
    def save_info_intro_grade(self):    
        # 创建电影简介.txt， 提取内容（演职人员，剧情简介），写入文件
        intro_file_name = self.dir_name + '/' + self.movie_name + u'简介.txt'
        intro_file = open(intro_file_name, 'a')
        
        #   演职人员介绍, parse_info 
        info = remove_tags(self.info) + '\n' + '#'*99 + '\n'
        intro_file.write(info.encode('utf8'))
        #   剧情简介 parse_intro
        intro_content = remove_tags(self.intro_con)
        intro_file.write(intro_content.encode('utf8'))
        intro_file.close()
        
        # 电影评分(9.6).txt 提取链接稍微麻烦，不是重点，暂不处理
        grade_file_name = self.dir_name + '/' + u'豆瓣评分' + '(' + self.grade + ').txt'
        grade = open(grade_file_name, 'a')
        grade_content = remove_tags(self.grade_con).replace(' ', '')       # 去除多余空格
        grade_content = grade_content.replace(u'\u661f\n\n\n', u'\u661f:')  # 去除多余换行，保留部分 5星:81.4%
        grade.write(grade_content.encode('utf8'))
        grade.close()
        
    # 生成图片保存目录 ./photos， 生成奖项介绍 获奖情况.txt ， 生成影评文件夹 ./影评
    def create_photos_dir(self, ):
        self.photos_dir = self.dir_name + '/' + 'photos'
        if not os.path.exists(self.photos_dir):
            os.mkdir(self.photos_dir)
    
    def create_wards_file(self, ):
        awards_file_name = self.dir_name + '/' + self.movie_name + u'获奖情况.txt'
        self.awards_file = open(awards_file_name, 'a')
    
    def create_reviews_dir_files(self, ):
        self.reviews_dir = self.dir_name + '/' + 'reviews'
        if not os.path.exists(self.reviews_dir):
            os.mkdir(self.reviews_dir)
        grade_dir_list = [u'一星影评', u'二星影评', u'三星影评', u'四星影评', u'五星影评', ]
        for grade_dir in grade_dir_list:
            grd_dir = self.reviews_dir + '/' + grade_dir  # No.1--肖申克的救赎 The Shawshank Redemption (1994)/一星影评/
            if not os.path.exists(grd_dir):
                os.mkdir(grd_dir)
                self.reviews_dirs.append(grd_dir)  # 调用的时候先判断下位置
        
process = CrawlerProcess()
process.crawl(DouBanMovie)
process.start()
