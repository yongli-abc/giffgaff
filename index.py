#-*- coding:utf-8 -*-
from flask import Flask, g, request, render_template
import sqlite3, re

app = Flask(__name__)
app.debug = True
##################
# 一些全局配置变量
##################
DATABASE = "tmp/data.db"
ADMIN = "admin"
PASSWORD = "spread_giffgaff"
EMAIL_PATTERN = '^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$'
PHONE_PATTERN = '(1)(3\d|4[5,7]|5[0-3,5-9]|8[0,2,3,6-9])\D*(\d{4})\D*(\d{4})$'

##################
# 这里放一些辅助函数
##################

def connect_db():
    return sqlite3.connect(DATABASE)

def init_db():
    db = connect_db()
    with open('schema.sql') as f:
        db.cursor().executescript(f.read())
    db.commit()

# TODO: 增加email存在性检查
def valid_form(form):
    '''
    接收一个request.formd对象，检查各个field，返回错误字符串
    若验证成功，则返回空字符串
    '''
    my_errors = []

    # 邮箱验证
    email = form['email']
    if not email:
        my_errors.append("邮箱不能为空")
    elif not re.match(EMAIL_PATTERN, email):
        my_errors.append("请输入正确的邮箱")
    else:
        # New validation
        pass

    # 姓名验证
    name = form['name']
    if not name:
        my_errors.append("姓名不能为空")

    # 电话验证
    phone = form['phone']
    if not phone:
        my_errors.append("电话不能为空")
    elif not re.match(PHONE_PATTERN, phone):
        my_errors.append("请输入正确的电话")

    # 卡数验证
    nano_qty = int(form['nano_qty'])
    micro_qty = int(form['micro_qty'])
    if not nano_qty and not micro_qty:
        my_errors.append("至少选择一张卡")

    return my_errors

##################
# 下面均为视图处理函数
##################

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template("index.html", guest="neil")
    elif request.method == 'POST':
        my_errors = valid_form(request.form)
        if not my_errors:
            return "Valid is successful"
        else:
            return render_template("index.html", my_errors=my_errors, guest="neil")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return "This is an admin page"

@app.route('/enquiry')
def enquiry():
    return "This is the enquiry page"

if __name__ == "__main__":
    # 本地测试环境
    app.run()
else:
    # BAE发布环境
    from bae.core.wsgi import WSGIApplication
    application = WSGIApplication(app)
