# -*- coding: utf-8 -*-
from flask import Flask, g, request, render_template, session
from captcha.image import ImageCaptcha
import sqlite3, re, time, urllib2, json, random, sys
sys.path.insert(0, './mail')
from mail import send_email
from contextlib import closing
from flask_wtf import Form
from wtforms import StringField
from wtforms import SelectField
from wtforms import validators

app = Flask(__name__)
app.secret_key = "lajsdfljqoruoqwuerouzxocvuoz"
app.config.from_pyfile('settings.py', silent=True)  # 读入全局配置

##################
# 这里放一些辅助函数
##################

# 创建订单Form类，实现验证逻辑
class OrderForm(Form):
    email = StringField(u'邮箱', validators=[validators.DataRequired(u'邮箱不能为空'), validators.Regexp(app.config['EMAIL_PATTERN'], message=u'请输入正确的邮箱')])

    name = StringField(u'姓名', validators=[validators.DataRequired(u'姓名不能为空')])

    phone = StringField(u'电话', validators=[validators.DataRequired(u'电话不能为空'), validators.Regexp(app.config['PHONE_PATTERN'], message=u'请输入11位国内号码')])

    nano_qty = SelectField(u'Nano 卡数量', choices=[(str(i), str(i)) for i in range(5)], default='0')

    micro_qty = SelectField(u'Micro 卡数量', choices=[(str(i), str(i)) for i in range(5)], default='0')

    captcha = StringField(u'验证码', validators=[validators.DataRequired(u'验证码不能为空')])

    def validate_email(self, field):
        if field.errors:    # 若邮箱已有错误，不再进行唯一性检查
            return False
        else:   # 进行邮箱唯一性检查
            try:
                connect_db()
                cur = g.db.cursor()
                cur.execute("select email from entries where email='%s'" % field.data)
                data = cur.fetchall()
                if len(data) > 0:
                    field.errors.append(u"该邮箱已经申请过，请勿重复提交")
                    return False
            except Exception as e:
                field.errors.append(str(e))
            finally:
                cur.close()
                g.db.close()

            return True

    def validate_captcha(self, field):
        if field.errors:    # 若验证码已验证为空，则不再进行对比验证
            return False
        elif field.data != session['captcha']:
            field.errors.append(u'验证码错误')
            return False
        else:
            return True

    def validate(self):
        rv = Form.validate(self)
        # if not rv:
        #     return False
        print self.errors
        flag1 = True
        flag2 = True

        if self.nano_qty.data == '0' and self.micro_qty.data == '0':
            self.errors['whole'] = [u'至少选择一张卡']
            flag1 = False

        if self.csrf_token.errors:  # 修改CSRF缺失时的错误提示
            self.csrf_token.errors[0] = u'CSRF标志缺失'
            flag2 = False


        return rv and flag1 and flag2

def connect_db():
    g.db = sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def save_record(form):
    '''
    将验证成功的记录保存到sqlite中
    若数据库操作过程发生异常，捕获后将错误信息添加到errors中进行返回
    '''
    errors = []
    try:
        connect_db()
        g.db.execute("insert into entries (email, name, phone, nano_qty, micro_qty) values (?, ?, ?, ?, ?)", (form['email'], form['name'], form['phone'], form['nano_qty'], form['micro_qty']))
        g.db.commit()
    except Exception as e:
        errors.append(str(e))
    finally:
        g.db.close()
        return errors

def get_all_entries():
    try:
        # 获取所有条目
        errors = []
        connect_db()
        cur = g.db.cursor()
        cur.execute("select * from entries")
        results = cur.fetchall()
        cur.close()

        # 计算统计信息
        stats = {}
        stats['count'] = len(results)
        stats['nano_total'] = sum([row[4] for row in results])
        stats['micro_total'] = sum([row[5] for row in results])
    except Exception as e:
        errors.append(str(e))
    finally:
        g.db.close()
        return (results, stats, errors)

def generate_captcha():
    '''
    验证码生成函数。调用后讲生成一个4位数字的随机字符串captcha_str
    根据该字符串生成图片，存放在/static/captcha.png
    并设置session['captcha'] = captcha_str
    '''
    # 生成验证码
    captch_str = "".join([str(random.choice(range(0,10))) for i in range(4)])
    session['captcha'] = captch_str
    image = ImageCaptcha(width=118, height=38, font_sizes=(37,37,37))
    image.write(captch_str, "static/captcha.png")

@app.template_filter('randSuffix')
def randSuffix(original_url):
    '''
    为验证码图片请求地址末尾加上随机字符串，确保图片不会被缓存，每次都会请求最新图片
    '''
    suffix = str(int(time.time()*100))
    return original_url + "?" + suffix

##################
# 下面均为视图处理函数
##################
# 首页
@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = OrderForm()
    if form.validate_on_submit():
        # 表单被提交并且验证成功
        generate_captcha()

        # 存储数据
        # save_record(request.form)

        # 发送邮件
        # receiver_list = [(request.form['email'], request.form['name'])]
        # subject = 'giffgaff 订单确认'
        # text = "您的 giffgaff 订单已经确认！请等待我们的后续通知。\n预期将于5月底通知具体的领卡时间和地点。\n"
        # send_email(receiver_list, subject, text)

        return render_template("index.html", form=form, ok_flag=True)
    else:
        # 新表单或者有错误
        generate_captcha() # 刷新验证码
        return render_template("index.html", form=form)

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

        if username == app.config['ADMIN'] and password == app.config['PASSWORD']:
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

    if username == app.config['ADMIN'] and password == app.config['PASSWORD']:
        # 验证成功，获取所有数据
        results = get_all_entries()[0]
        return json.dumps(results)

# 查询页面
@app.route('/enquiry')
def enquiry():
    enquiry_email = request.args.get('email')
    delete = request.args.get('delete')
    if not enquiry_email:
        # 给出初始查询页面提示
        return render_template("enquiry.html")
    elif not delete:
        # 尝试查询
        result = []
        errors = []
        try:
            connect_db()
            cur = g.db.cursor()
            cur.execute("select * from entries where email='%s'" % enquiry_email)
            data = cur.fetchall()
            if len(data) > 0:
                result = data[0]
            cur.close()
        except Exception as e:
            errors.append(str(e))
        finally:
            g.db.close()
            if len(result) > 0:
                # 有查询结果
                return render_template("enquiry.html", result=result, errors=errors)
            else:
                # 无查询结果
                return render_template("enquiry.html", main_msg=u"查询不到该邮箱的预定信息！", msg_type="error", errors=errors)

    elif delete:
        # 进行删除
        errors = []
        try:
            connect_db()
            cur = g.db.cursor()
            cur.execute("delete from entries where email='%s'" % enquiry_email)
            cur.close()
        except Exception as e:
            errors.append(str(e))
        finally:
            g.db.commit()
            g.db.close()
            if cur.rowcount > 0:
                # 删除成功
                return render_template("enquiry.html", main_msg=u"预定信息删除成功！", msg_type="success", errors=errors)
                pass
            else:
                # 没有数据被影响
                return render_template("enquiry.html", main_msg=u"无法删除不存在的信息！", msg_type="error", errors=errors)


        return "Going to delete"

# 激活页面
@app.route('/activate')
def activate():
    return render_template("activate.html")

# 关于页面
@app.route('/about')
def about():
    return render_template("about.html")

# 404错误页面
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    # 本地测试环境
    app.debug = True    # 只在测试环境开启 debug
    app.run()
else:
    try:
        # BAE发布环境
        from bae.core.wsgi import WSGIApplication
        application = WSGIApplication(app)
    except ImportError:
        print "Not in BAE context"
