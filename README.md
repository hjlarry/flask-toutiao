### 一、大量的使用缓存

redis中存储了这些东西: 
1. post和comment的content
2. 通过corelib.mc中的cache装饰器的func结果
3. 通过Model.cache.query查询得到的结果，往往用在model.get上，但好像使用2中的cache装饰器也能实现
4. 通过CRUD时加减目标计数而无需数据库count


疑惑:
1. dogpile.cache的作用是什么？
查了下dogpile是指刚好缓存失效时，大量并发导致服务器挂掉，那么这个库的作用是通过锁线程限制数据库查询？
2. walrus的作用是什么?
感觉项目里没有用到，实际上一直都用的set get delete等基础方法，而这些方法都是redis-py本身提供的


### 二、 sqlalchemy的使用
1. 避免使用外键约束
2. with_entities的使用
3. target_id/target_kind的使用

疑惑:
1. 有的表设了'mysql_charset': 'utf8'，是否没有str相关字段的表都应该这样设置去节省空间?
2. Contact.clear_mc方法中有:
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
这时候的st是另一个session的对象，再去save()是会报错的，应该再去查询一下？
### 三、 mixin


### 四、 crawldata的方式


### 五、 elesticsearch的使用