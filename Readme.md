### 简介
一个简单的抓取知乎所有问题的小爬虫，通过该爬虫可建立知乎的问题种子库，便于抓取热
门问题和回答，或满足其它的需求.

### 使用说明
1、修改 settings.yaml 中的 ‘EMAIL’ 和 'PASSWORD' 字段.  
2、执行

```python
$ python zhihu.py
```

即可.

### 注意
1、数据默认存储在当前目录下名为 db.txt 的文本中，使用时可根据自己的需求，修改源
码中存储数据的代码.
2、默认只抓取如下几个字段:

* 问题名
* 问题的 url
* 提问者名字
* 提问者的主页 url
* 提问时间

可根据自己的需求，修改 **_parse_page()** 方法中的页面解析部分.  
3、默认采用单线程抓取，抓取速度很慢。其实通过这个小爬虫就可以看出请求的规则，有
兴趣可以尝试多进程/多线程或用 Gevent 进行并行抓取，很简单，但要注意控制好抓取频
率，防止因为给知乎服务器带来太大压力而被封.(**慎重考虑**)
