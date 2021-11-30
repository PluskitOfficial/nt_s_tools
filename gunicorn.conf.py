import os
import multiprocessing
# 工作目录
chdir = os.path.dirname(os.path.abspath(__file__))
# 自动重启
reload = True
# 绑定的ip与端口
bind = "0.0.0.0:10010"
# 以守护进程的形式后台运行
daemon = False
# 工作进程类型(默认的是 sync 模式，还包括 eventlet, gevent, or tornado, gthread, gaiohttp)
worker_class = 'gevent'
# 工作进程数
workers = 2  # multiprocessing.cpu_count()
# 指定每个工作进程开启的线程数
threads = 4  # multiprocessing.cpu_count() * 2
# 最大挂起的连接数，64-2048
backlog = 512
# 超时
timeout = 30
# 调试状态
debug = False
# 访问日志文件，"-" 表示标准输出
accesslog = "-"
# 错误日志文件，"-" 表示标准输出
errorlog = "-"
# 日志格式
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
# 其每个选项的含义如下：
'''
h          remote address
l          '-'
u          currently '-', may be user name in future releases
t          date of the request
r          status line (e.g. ``GET / HTTP/1.1``)
s          status
b          response length or '-'
f          referer
a          user agent
T          request time in seconds
D          request time in microseconds
L          request time in decimal seconds
p          process ID
'''
