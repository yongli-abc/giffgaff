#-*- coding:utf-8 -*-
from flask import Flask, g, request

app = Flask(__name__)
app.debug = True

@app.route('/')
def hello():
    return "Hello, world! - Flask\n"

if __name__ == "__main__":
    # 本地测试环境
    app.run()
else:
    # BAE发布环境
    from bae.core.wsgi import WSGIApplication
    application = WSGIApplication(app)
