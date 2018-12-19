### 一、大量的使用缓存

redis中存储了这些东西: 
1. post和comment的content
2. 通过corelib.mc中的cache装饰器的func结果
3. 通过Model.cache.query查询得到的结果，往往用在model.get上，但好像使用2中的cache装饰器也能实现
4. 通过CRUD时加减目标计数而无需数据库count
5. feed 相关

本地进程内缓存，在通过redis获取属性时把结果写入一个字典便于相同属性请求不需走redis，redis设置值、删除值时清楚该本地缓存。localcache中存储了post和comment的content。


### 二、 sqlalchemy的使用
1. 避免使用外键约束，查询时往往是通过with_entities进行了多次查询
2. obj.delete(synchronize_session="fetch")
3. 一对多关系时，"多"的target_id可以存储"一"的id，"多"的target_kind可以存储"一"的kind，例如点赞表就可以通过kind区分点赞的是文章还是评论。这样设置索引时要注意设置成一个id+kind的联合索引。
4. 考虑从业务角度限制一些model的功能，比如限制Contact的update
5. __declare_last__结合flush event的使用 
6. 事务隔离级别采用读已提交
7. 通过mixin将一些model解耦，不同的继承达到不同的功能



### 三、 flask的使用
1. 封装一个Request类用于拿到request.user
2. 添加teardown_request钩子用于异常时数据库事务回滚
3. json_api 结合 schema
4. add_template_global 和 context_processor
5. get_template_attribute 拿模板内容


### 其他
1. 抓取内容时可以使用解析feed的方式，很方便

2. celery任务添加flask上下文的方法

3. iconfont使用

4. elesticsearch的使用，以及通过高斯函数特性（衰减先慢后快再慢）得到一个热门分享的算法


### 这些地方我觉得可能是个bug

1. Contact.clear_mc方法中有:
```
st = userFollowStats.get_or_create(to_id)
st.save()
```
这时候若st是没有的，其新建过程:
```
if not st:
    session = db.create_scoped_session()
    st = cls(id=id)
    session.add(st)
    session.commit()
return st
```
这时候的st是另一个session的对象，再去save()是会报错的，我的解决方案是重新再次查询了一下


2. 注册发送确认邮件时并未发送我们在templates定义的邮件html页面内容
这是因为flask_security.utils.send_mail()方法中，有一行代码不同导致：
```
# flask_security的官方仓库的develop分支以及董大那个版本
msg.html = _security.render_template('%s/%s.html' % ctx, **context)
# flask_security的官方仓库的master分支，也就是直接pip install的版本
msg.html = render_template('%s/%s.html' % ctx, **context)  
```
感觉好坑，其官方文档明确说了替换这些email模板很容易，结果一个3.0的主版本已经发布了一年了还不更新还有这bug
也可以通过自定义send_mail方法来避免修改flask_security的源码解决这个问题，官方文档有写


3. 项目里所有用到zadd的地方需要改一下，因为redis-py 3.0以上修改了:
* ZADD now requires all element names/scores be specified in a single
  dictionary argument named mapping. This was required to allow the NX,
  XX, CH and INCR options to be specified.


4. 我使用flask_dance替代social-oauth。因为依据当前flask_security的配置某用户要登陆成功就必须active字段是true且confirm_at字段有值，flask_dance可以通过外部去介入其创建用户的过程，social-oauth可能要修改源码。使用flask_dance本地测试时因为HTTPS的问题需要export OAUTHLIB_INSECURE_TRANSPORT=1


5. card.js中的是否点赞收藏判断逻辑是$('.like-button').hasClass('liked')，那么在列表页中有任一条被点赞过则该判断都是True.我前端太菜这块还不会改


6. Feed.get_user_feed()中：
```
start = (page - 1) * PER_PAGE
end = start + PER_PAGE 
post_ids = rdb.zrange(feed_key, start, end)
```
假设要每页显示3个，那么start是0，end是3，post_ids就是4个元素，我改为了end-1


### 还有这些地方比较疑惑

1. dogpile.cache的作用是什么？
查了下dogpile是指刚好缓存失效时，大量并发导致服务器挂掉，那么这个库的作用是通过锁线程限制数据库查询？


2. 有的表设了'mysql_charset': 'utf8'，是否没有str相关字段的表都应该这样设置去节省空间?