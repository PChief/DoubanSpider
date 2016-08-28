# DoubanSpider
Scrapy douban movie top250 and book top250

movie top250  https://movie.douban.com/top250

book top250 https://book.douban.com/top250?icn=index-book250-all

For movies:

download the pages, extract data like movie name,photos, description, and most important , reviews, then save them as follows:

./No.1--肖申克的救赎 The Shawshank Redemption (1994)
    
    肖申克的救赎简介.txt  from https://movie.douban.com/subject/1292052/
        内容：
            导演:
                    弗兰克·德拉邦特
            编剧: 
                    弗兰克·德拉邦特
                    斯蒂芬·金
           主演: 
                    蒂姆·罗宾斯
                    摩根·弗里曼
                    鲍勃·冈顿
                    ......
          剧情简介：
                 20世纪40年代末，小有成就的青年银行家安迪（蒂姆·罗宾斯 Tim Robbins 饰）因涉嫌杀害妻子及她的情人而锒铛入狱。
                        .......
           获奖情况(https://movie.douban.com/subject/1292052/awards/)：
                 第67届奥斯卡金像奖(link) 最佳影片(提名)   尼基·马文  (link)
                 .......
    豆瓣评分(9.6).txt     from https://movie.douban.com/subject/1292052/
    五星影评.txt    （from  https://movie.douban.com/subject/1292052/reviews）
    *****命名都是非常有规律的，可以通过Rule规则匹配****
      十年 肖申克的救赎
       《肖申克的救赎》与斯德哥尔摩综合症－－你我都是患者
          ...
     一星影评.txt

    ./imgs   (from  https://movie.douban.com/subject/1292052/photos?type=S&start=40&sortby=vote&size=a&subtype=a)


For books:

download the pages, extract data like book names, photos, description, reviews and notes. then save them as follows:

 ./1--小王子（9.0）-[法]圣埃克苏佩里
 
      小王子简介.txt
      [法]圣埃克苏佩里简介.txt
      小王子书评.txt
      小王子读书笔记.txt
     （书评与书评之间，笔记与笔记之间由99个星号('*'*99)隔开）
