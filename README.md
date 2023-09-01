# aio-frp-python
基于python异步IO实现的frp内网穿透
## 使用方法
frp-python 使用方法示例
假设服务端ip是110.110.110.1，要穿透本机的远程桌面端口3389，则分别在服务端和本机如下启动：

服务端

```shell
python frps.py --serve_host 0.0.0.0 --serve_port 8800 --user_host 0.0.0.0 --user_port 8801
```

客户端

```shell
python frpc.py --serve_host 110.110.110.1 --serve_port 8800 --local_host localhost --local_port 3389
```
然后通过110.110.110.1:8001就可以远程访问本机了！
