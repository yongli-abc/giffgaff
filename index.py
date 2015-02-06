# -*- coding: utf-8 -*-
from flask import Flask, g, request, render_template, session
import sqlite3, re, time, urllib2, json

app = Flask(__name__)
app.debug = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
##################
# 一些全局配置变量
##################
DATABASE = "tmp/data.db"
ADMIN = "admin"
PASSWORD = "admin"
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

def valid_form(form):
    '''
    接收一个request.formd对象，检查各个field，返回错误字符串
    若验证成功，则返回空字符串
    '''
    errors = []

    # 邮箱验证
    email = form['email']
    if not email:
        errors.append(u"邮箱不能为空")
    elif not re.match(EMAIL_PATTERN, email):
        errors.append(u"请输入正确的邮箱")
    else:
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("select email from entries where email='%s'" % email)
            data = cur.fetchall()
            if len(data) > 0:
                errors.append(u"该邮箱已经申请过，请勿重复提交")
            cur.close()
        except Exception as e:
            errors.append(str(e))
        finally:
            conn.close()

    # 姓名验证
    name = form['name']
    if not name:
        errors.append(u"姓名不能为空")

    # 电话验证
    phone = form['phone']
    if not phone:
        errors.append(u"电话不能为空")
    elif not re.match(PHONE_PATTERN, phone):
        errors.append(u"请输入正确的电话")

    # 卡数验证
    nano_qty = int(form['nano_qty'])
    micro_qty = int(form['micro_qty'])
    if not nano_qty and not micro_qty:
        errors.append(u"至少选择一张卡")

    if not errors:
        # 检查验证码
        r = urllib2.urlopen("http://captchator.com/captcha/check_answer/%s/%s" % (session['id'], form['captcha']))
        if not int(r.read()):
            errors.append(u"验证码输入错误")

    return errors

def save_record(record):
    '''
    将验证成功的记录保存到sqlite中
    若数据库操作过程发生异常，捕获后将错误信息添加到errors中进行返回
    '''
    errors = []
    try:
        conn = connect_db()
        conn.execute("insert into entries (email, name, phone, nano_qty, micro_qty) values (?, ?, ?, ?, ?)", (record['email'], record['name'], record['phone'], record['nano_qty'], record['micro_qty']))
        conn.commit()
    except Exception as e:
        errors.append(str(e))
    finally:
        conn.close()
        return errors

##################
# 下面均为视图处理函数
##################
# 首页
@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # 若首次访问，设置会话id
        if not session.has_key('id'):
            session['id'] = int(time.time()*10)

        return render_template("index.html")
    elif request.method == 'POST':
        # 若获取POST请求时，未设置会话id，则使用get方法重新定向
        if not session.has_key('id'):
            return redirect(url_for('index'))

        errors = valid_form(request.form)
        if not errors:
            # 表单验证成功，保存数据
            record = {
                'email':request.form['email'],
                'name':request.form['name'],
                'phone':request.form['phone'],
                'nano_qty':int(request.form['nano_qty']),
                'micro_qty':int(request.form['micro_qty']),
            }
            errors = save_record(record)
            if not errors:
                return render_template("index.html", ok_flag=True)
            else:
                return render_template("index.html", errors=errors)
        else:
            # 表单验证失败，返回带错误信息的模版
            return render_template("index.html", errors=errors)

def get_all_entries():
    try:
        # 获取所有条目
        errors = []
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("select * from entries")
        results = cur.fetchall()
        cur.close()

        # 计算统计信息
        stats = {}
        stats['count'] = len(results)
        stats['nano_total'] = sum([row[4] for row in results])
        stats['micro_total'] = sum([row[5] for row in results])
        print stats
    except Exception as e:
        errors.append(str(e))
    finally:
        conn.close()
        return (results, stats, errors)


# 后台页面
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        if session.has_key("admin_flag"):
            results, stats, errors = get_all_entries()
            return render_template("admin.html", results=results, stats=stats, errors=errors)
        else:
            return render_template("admin.html")

    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN and password == PASSWORD:
            # 输入正确，设置session，下次直接进入后台
            if not session.has_key("admin_flag"):
                session['admin_flag'] = True

            results, stats, errors = get_all_entries()

            return render_template("admin.html", results=results, stats=stats, errors=errors)
        else:
            # 登陆验证失败
            return render_template("admin.html", errors = [u"输入错误"])

# 后台json api
@app.route('/admin/json', methods=['POST'])
def adminJson():
    username = request.form['username']
    password = request.form['password']

    if username == ADMIN and password == PASSWORD:
        # 验证成功，获取所有数据
        results = get_all_entries()[0]
        return json.dumps(results)

# 查询页面
@app.route('/enquiry')
def enquiry():
    enquiry_email = request.args.get('email')
    if not enquiry_email:
        # 给出初始查询页面提示
        return render_template("enquiry.html")
    else:
        # 尝试查询
        result = []
        errors = []
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("select * from entries where email='%s'" % enquiry_email)
            data = cur.fetchall()
            if len(data) > 0:
                result = data[0]
            cur.close()
        except Exception as e:
            errors.append(str(e))
        finally:
            conn.close()
            return render_template("enquiry.html", result=result, errors=errors)

# 关于页面
@app.route('/about')
def about():
    return render_template("about.html")

if __name__ == "__main__":
    # 本地测试环境
    app.run()
else:
    # BAE发布环境
    from bae.core.wsgi import WSGIApplication
    application = WSGIApplication(app)
