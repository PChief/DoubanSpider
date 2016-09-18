# DoubanSpider


**Scrape douban movie top250 and book top250**

   movie top250  https://movie.douban.com/top250

   book top250 https://book.douban.com/top250?icn=index-book250-all

**For movies:**

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
        肖申克的救赎获奖情况.txt  (https://movie.douban.com/subject/1292052/awards/)：
                 第67届奥斯卡金像奖(link) 最佳影片(提名)   尼基·马文  (link)
                 .......
        豆瓣评分(9.6).txt     from https://movie.douban.com/subject/1292052/
        ./五星影评    （from  https://movie.douban.com/subject/1292052/reviews）
        *****命名都是非常有规律的，可以通过Rule规则匹配****
        十年 肖申克的救赎.txt
        《肖申克的救赎》与斯德哥尔摩综合症－－你我都是患者.txt
          ...
        ./一星影评

        ./imgs   (from  https://movie.douban.com/subject/1292052/photos?type=S&start=40&sortby=vote&size=a&subtype=a)


**For books:**

download the pages, extract data like book names, photos, description, reviews and notes. then save them as follows:

     ./1--小王子（9.0）-[法]圣埃克苏佩里
 
        小王子简介.txt
        [法]圣埃克苏佩里简介.txt
        ./reviews
            书评1.txt
            书评2.txt
            ...
        ./annotations
            笔记1.txt
            笔记2.txt
            ...
     

**Examples for saved files：**

1）Top50 movie

![image](https://github.com/PChief/DoubanSpider/blob/master/Douban/imgs/%E5%89%8D50%E4%B8%AA%E7%94%B5%E5%BD%B1.png)

2）The Shawshank Redemption/肖申克的救赎

![image](https://github.com/PChief/DoubanSpider/blob/master/Douban/imgs/%E8%82%96%E7%94%B3%E5%85%8B%E7%9A%84%E6%95%91%E8%B5%8E%E4%BA%94%E6%98%9F%E5%BD%B1%E8%AF%84.png)

3）Photoes for The Shawshank Redemption/肖申克的救赎图片（剧照、海报、壁纸）

![image](https://github.com/PChief/DoubanSpider/blob/master/Douban/imgs/%E8%82%96%E7%94%B3%E5%85%8B%E7%9A%84%E6%95%91%E8%B5%8E%E5%9B%BE%E7%89%87.png)

4)  Douban book/豆瓣读书-1988我想和这个世界谈谈

![image](https://github.com/PChief/DoubanSpider/blob/master/Douban/imgs/%E8%B1%86%E7%93%A3%E8%AF%BB%E4%B9%A6-1988%E6%88%91%E6%83%B3%E5%92%8C%E8%BF%99%E4%B8%AA%E4%B8%96%E7%95%8C%E8%B0%88%E8%B0%88.png)
