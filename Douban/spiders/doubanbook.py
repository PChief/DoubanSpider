# _*_ coding:utf8 _*_

import scrapy
import os
from w3lib.html import remove_tags
from scrapy.crawler import CrawlerProcess

# 爬取豆瓣读书top250 （https://book.douban.com/top250?icn=index-book250-all）
class DouBanBook(scrapy.Spider):
    
    name = 'doubanbook'
    allowed_domains = ['douban.com', 'doubanio.com']
    start_urls = ['https://book.douban.com/top250?start=0',
                  'https://book.douban.com/top250?start=25',
                  'https://book.douban.com/top250?start=50',
                  'https://book.douban.com/top250?start=75',
                  'https://book.douban.com/top250?start=100',
                  'https://book.douban.com/top250?start=125',
                  'https://book.douban.com/top250?start=150',
                  'https://book.douban.com/top250?start=175',
                  'https://book.douban.com/top250?start=200',
                  'https://book.douban.com/top250?start=225',]
    # start_urls = ['https://book.douban.com/subject/1084336/']  # 测试用开始链接，小王子

    """
    从链接 (https://book.douban.com/subject/1084336/)依次提取：
    a）书籍概况(原始图片、基本信息div[@id="info"])
    b）豆瓣评分(//div[@class="rating_wrap clearbox"])
    c）内容简介(//span[@class="all hidden"]//div[@class="intro"])
    d）作者简介((//div[@class="article"]//div[@class="related_info"]//div/div[@class="intro"])[2])
    e）目录(//div[@class="indent"][contains(@id,"short")] 或者  //*[@class="indent"][@style="display:none"])
    f) 书评链接，再进一步提取书评(//div[@id="reviews"]/div[@id="wt_0"]/p/a/@href)
    书评必须访问书评链接才能提取书评内容
    g) 笔记链接，再进一步提取笔记(//div[@class="ugc-mod reading-notes"]/div[@class="ft"]/p/a/@href)
    笔记可以在页面中找到隐藏的项目，进而可以直接提取出来内容
    """

    def parse(self, response):
        # 提取出每个页面的25个url
        subj_xpath = '//div[@class="pl2"]/a/@href'
        subj_urls = response.xpath(subj_xpath).extract()
        for subj_url in subj_urls:
            yield scrapy.Request(url=subj_url, callback=self.parse_book_subject, dont_filter=True)

    def parse_book_subject(self, response):
        # step 1: extract data from book link
        # step 1.1 : 创建目录（小王子--[法]圣埃克苏佩里）
        book_name_xpath = '//div[@id="wrapper"]/h1/span/text()'
        author_name_xpath = '//div[@id="info"]/span[1]/a/text()'
        book_name = response.xpath(book_name_xpath).extract()[0]  # u'小王子'
        book_name = self.clean_invilad_chracter(book_name)
        author_name = response.xpath(author_name_xpath).extract()[0]  # u'[法] 圣埃克苏佩里'
        author_name = self.clean_invilad_chracter(author_name)
        book_dir = book_name + '--' + author_name  
        if not os.path.exists(book_dir):
            os.mkdir(book_dir)
        self.save_subject_profile(response=response, book_dir=book_dir, book_name=book_name, author_name=author_name)
        
        # step 1.4 : extract reviews_link and annotations_link, yield them
        # step 1.4.1  : reviews
        reviews_link_xpath = '//div[@id="reviews"]/div[@id="wt_0"]/p/a/@href'
        reviews_link = response.xpath(reviews_link_xpath).extract()[0]
        # https://book.douban.com/subject/1084336/reviews
        reviews_dir = book_dir + '/' + 'reviews'
        if not os.path.exists(reviews_dir):
            os.mkdir(reviews_dir)
        print '*'*50,reviews_link
        rqst_reviews_link = scrapy.Request(url=reviews_link, callback=self.parse_rvws_ants, dont_filter=True)
        rqst_reviews_link.meta['path'] = reviews_dir
        rqst_reviews_link.meta['xpath_urls'] = '//*[@class="review-list"]//div/header/h3/a/@href'
        rqst_reviews_link.meta['xpath_next_page'] = '//span[@class="next"]/link/@href'
        rqst_reviews_link.meta['callback'] = self.parse_review
        yield rqst_reviews_link

        # step 1.4.2  : annotations
        annotations_link_xpath = '//div[@class="ugc-mod reading-notes"]/div[@class="ft"]/p/a/@href'
        # https://book.douban.com/subject/1084336/annotation
        try:
            annotations_link = response.xpath(annotations_link_xpath).extract()[0]
            # https://book.douban.com/subject/1084336/annotation
            annotations_dir = book_dir + '/' + 'annotations'
            if not os.path.exists(annotations_dir):
                os.mkdir(annotations_dir)
            rqst_annotations_link = scrapy.Request(url=annotations_link, callback=self.parse_rvws_ants, dont_filter=True)
            rqst_annotations_link.meta['path'] = annotations_dir
            rqst_annotations_link.meta['xpath_urls'] = None  # 直接从页面中提取内容
            rqst_annotations_link.meta['xpath_next_page'] = '//span[@class="next"]/link/@href'
            rqst_annotations_link.meta['callback'] = None
            yield rqst_annotations_link
        except IndexError:
            print 'Annotations is less ,from ', response.url
        
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
        book_profile_xpath = '//div[@id="info"]'
        book_grade_xpath = '//div[@class="rating_wrap clearbox"]'
        book_intro_xpath = '//span[@class="all hidden"]//div[@class="intro"]'
        # 有的没有目录，有的目录很少，只提取目录较完整的部分（红楼梦）
        book_catalogue_display_xpath = '//*[@class="indent"][@style="display:none"]'
        author_intro_xpath = '//*[@id="content"]/div/div[1]/div[3]/div[2]/div/div'
        
        # step 1.2 : extract book_profile , book_grade, book_intro, book_catalogue, save them
        book_profile = response.xpath(book_profile_xpath).extract()[0]
        book_profile = self.remove_needless_sysmbols(remove_tags(book_profile))
        book_grade = response.xpath(book_grade_xpath).extract()[0]
        book_grade = remove_tags(book_grade).replace(u'\u661f\n\n\n            \n\n\n            ', u'\u661f ')
        book_grade = self.remove_needless_sysmbols(book_grade)
        book_grade_mark = book_grade[6:9]  # u'9.0'

        # 图书简介过长部分会被隐藏，xpath需分两种情况
        try:
            book_intro = response.xpath(book_intro_xpath).extract()[0]
            book_intro = remove_tags(book_intro)
            book_intro = u'内容简介:\n\n' + book_intro
        except IndexError:
            try:
                book_intro_xpath = '//*[@id="link-report"]/div[1]/div'
                book_intro = response.xpath(book_intro_xpath).extract()[0]
                book_intro = remove_tags(book_intro)
                book_intro = u'内容简介:\n\n' + book_intro
            except IndexError:
                book_intro = u'内容简介:  暂无\n\n'

        # 有的没有目录，有的目录很少，只提取目录较完整的部分（红楼梦）
        try:
            book_catalogue = response.xpath(book_catalogue_display_xpath).extract()[0]
            book_catalogue = remove_tags(book_catalogue)
        except IndexError:
            book_catalogue = u'目录:  太少或无\n'

        book_file_name = book_dir + '/' + book_dir + '(' + book_grade_mark + ').txt'
        book_file = open(book_file_name, 'a')
        write_book_con = book_name + '\n\n' + \
                         book_profile + '\n\n' + \
                         book_grade + '\n\n' + \
                         book_intro + '\n\n' + \
                         book_catalogue + '\n\n'
        book_file.write(write_book_con.encode('utf8'))
        book_file.close()
        
        # step 1.3 : extract author intro, save it
        author_intro_file_name = book_dir + '/' + author_name + u'简介.txt'
        author_intro_file = open(author_intro_file_name, 'a')
        # 作者介绍同样有多有少，区别对待
        try:
            author_intro = response.xpath(author_intro_xpath).extract()[0]
            author_intro = remove_tags(author_intro)
        except IndexError:
            try:
                author_intro_xpath = '//*[@id="content"]/div/div[1]/div[3]/div[2]/span[2]/div'
                author_intro = response.xpath(author_intro_xpath).extract()[0]
                author_intro = remove_tags(author_intro)
            except IndexError:
                author_intro = u'\n作者介绍:  暂缺\n\n'
        write_author_con = author_name + u'简介' + '\n\n' + author_intro
        author_intro_file.write(write_author_con.encode('utf8'))
        author_intro_file.close()
    
    def parse_rvws_ants(self, response):
        """
        参数说明
        path: 保存书评文件、笔记文件的目录
        xpath_urls: 用于提取页面中review的URL列表，笔记不需要
        xpath_next_page: 用于提取下一页的链接后缀，需要加上base_url才能访问
        callback: 请求单个review页面的回调函数，笔记不需要
        """
        print response.url
        
        if response.meta['xpath_urls']:
            # 提取review的链接，再进一步提取内容
            rvws_uants_url_list_xpath = response.meta['xpath_urls']
            rvws_uants_url_list = response.xpath(rvws_uants_url_list_xpath).extract()
            for rvw_uant_url in rvws_uants_url_list:
                rqst = scrapy.Request(url=rvw_uant_url, callback=response.meta['callback'], dont_filter=True)
                rqst.meta['path'] = response.meta['path']
                yield rqst
        else:
            # 提取笔记内容，保存
            annotations_xpath = '//li[@class="ctsh clearfix"]'
            # 每页最多十个，均为li标签的原始内容
            annotations_raw = response.xpath(annotations_xpath).extract()
            self.extract_annotation(annotations_raw=annotations_raw, path=response.meta['path'])
        
        # parse next reviews or annotations page
        base_url = response.url.split('?')[0]
        next_page_url_xpath = response.meta['xpath_next_page']
        next_page_url = response.xpath(next_page_url_xpath).extract()
        if next_page_url:
            # 如果列表为空，说明没有下一页
            next_page_url = base_url + next_page_url[0]
            # 递归调用自身
            rqst_next_page = scrapy.Request(url=next_page_url, callback=self.parse_rvws_ants, dont_filter=True)
            rqst_next_page.meta['path'] = response.meta['path']
            rqst_next_page.meta['xpath_urls'] = response.meta['xpath_urls']
            rqst_next_page.meta['xpath_next_page'] = response.meta['xpath_next_page']
            rqst_next_page.meta['callback'] = response.meta['callback']
            yield rqst_next_page
    

        
    def parse_review(self, response):
        print response.url
        """
        提取内容；
        title       //span[@property="v:summary"]/text()
        title_link  response.url
        author      //span[@property="v:reviewer"]/text()
        author_link  //header/a[1]/@href
        author_icon_img_src  //a[@class="avatar author-avatar left"]/img/@src
        grade      //span[contains(@class,"main-title-rating")]/@class   --> "allstar50 main-title-rating"
        content    //div[@property="v:description"]
        (content 在remove_tags时保留a标签，或者提取出里面的链接，注意换行，避免所有文本拥挤在一个地方)
        """
        title = response.xpath('//span[@property="v:summary"]/text()').extract()[0]
        title = self.clean_invilad_chracter(title)
        title_link = response.url
        author_name = response.xpath('//span[@property="v:reviewer"]/text()').extract()[0]
        author_name = self.clean_invilad_chracter(author_name)
        author_link = response.xpath('//header/a[1]/@href').extract()[0]
        author_icon_img_src_xpath = '//a[@class="avatar author-avatar left"]/img/@src'
        author_icon_img_src = response.xpath(author_icon_img_src_xpath).extract()[0]
        author_icon_img_src = author_icon_img_src.replace('icon/u', 'icon/ul')  # 替换为大图链接
        try:
            grade = response.xpath('//span[contains(@class,"main-title-rating")]/@class').extract()[0]
            grade = grade.split()[0][-2:-1]  # u'5'
        except IndexError:
            grade = u'1'  # 没有打星的按照一星计算
        content = response.xpath('//div[@property="v:description"]').extract()[0]  # 处理content
        content = remove_tags(content)
        path = response.meta['path']
        review_file_name = path + '/' + title + '--' + author_name + '--' + grade + 'stars.txt'
        review_file = open(review_file_name, 'a')
        review_con = title + '\n' + \
                     title_link + '\n' +\
                     u'作者:' + author_name + '\n' +\
                     u'作者链接: ' + author_link + '\n\n' + \
                     content
        review_file.write(review_con.encode('utf8'))
        review_file.close()
        rqst_author_icon = scrapy.Request(url=author_icon_img_src, callback=self.save_author_icon, dont_filter=True)
        rqst_author_icon.meta['path'] = path
        yield rqst_author_icon

    def extract_annotation(self, annotations_raw, path):
        for annotation_raw in annotations_raw:
            """
            保存内容：
            title       div[@class="con"]/div[@class="nlst"]/h3/a/text()
            title_link  div[@class="con"]/div[@class="nlst"]/h3/a/@href
            author      div[@class="ilst"]/a/img/@alt
            author_link div[@class="ilst"]/a/@href
            author_icon_img_src  div[@class="ilst"]/a/img/@href
                https://img3.doubanio.com/icon/u3393285-50.jpg
                https://img3.doubanio.com/icon/ul3393285-50.jpg
            grade       div[@class="con"]/div[@class="clst"]/p[@class="user"]/span/@class --> allstar40
            content     div[@class="all hidden"]
            剔除内容里面的不相干内容，如“回应”二字
            """
            ann_sel = scrapy.Selector(text=annotation_raw)  # 文本对象转为selector对象
            try:
                title = ann_sel.xpath('//div[@class="nlst"]/h3/a/text()').extract()[0]
                title = self.clean_invilad_chracter(title)
                title_link = ann_sel.xpath('//div[@class="nlst"]/h3/a/@href').extract()[0]
            except IndexError:
                title = 'No title'
                title_link = 'Null'
            author = ann_sel.xpath('//div[@class="clst"]/p/a/text()').extract()[0]
            author = self.clean_invilad_chracter(author)
            author_link = ann_sel.xpath('//div[@class="clst"]/p/a/@href').extract()[0]
            author_icon_img_src_xpath = '//div[@class="ilst"]/a/img/@src'
            author_icon_img_src = ann_sel.xpath(author_icon_img_src_xpath).extract()[0]
            try:
                grade = ann_sel.xpath('//div[@class="clst"]/p/span/@class').extract()[0]
                grade = grade.split()[0][-2:-1]  # u'5'
            except IndexError:
                grade = u'1'  # 没有打星的按照一星计算

            # 处理content
            content = ann_sel.xpath('//div[@class="all hidden"]').extract()[0]
            content_sel = scrapy.Selector(text=content)
            clear_con = content_sel.xpath('//div[@class="col-rec-con clearfix"]').extract()[0]
            content = content.replace(clear_con, '').replace('<div style="padding-bottom:1em;"></div>', '\n')
            content = remove_tags(content)

            annotation_file_name = path + '/' + title + '--' + author + '--' + grade + '.txt'
            annotation_file = open(annotation_file_name, 'a')
            annata_wire_con = title + '\n' + \
                              title_link + '\n' + \
                              u'作者： ' + author + '\n' + \
                              u'作者链接：' + author_link + \
                              content
            annotation_file.write(annata_wire_con.encode('utf8'))
            annotation_file.close()
    
    def save_author_icon(self, response):
        path = response.meta['path']
        # 有的头像为小图，转为大图链接后，响应的返回值为404，scrapy自动丢弃不处理了
        icon_file_name = path + '/' + response.url.split('/')[-1]
        icon_file = open(icon_file_name, 'wb')
        icon_file.write(response.body)
        icon_file.close()

    def remove_needless_sysmbols(self, text=''):
        # 删除多余的符号，默认删除多余的'\n' '/r/n'
        text = text.replace('\r\n', '\r').replace('\n ', ' ')
        for sysmbol in [' ', '\r', '\n', ]:
            double_sysmbols = sysmbol * 2
            while double_sysmbols in text:
                text = text.replace(double_sysmbols, sysmbol)
        return text

    def clean_invilad_chracter(self, strings, invalid_chr=r'\/:*?"<>|'):
        # 剔除非法字符
        for chr in invalid_chr:
            strings = strings.replace(chr, '')
        return strings

process = CrawlerProcess()
process.crawl(DouBanBook)
process.start()
