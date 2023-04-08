# --*-- coding:utf8 --*--
import requests

# url = "https://api.mailgun.net/v2/sandboxca42fed017ca4ec7ae250e36e7560562.mailgun.org/messages"
# api = "key-3d46b25039688ecfd3c36dd68e660395"
# sender = "spread_giffgaff@yongli1992.com"
#
# def send_email(receiver_list, subject, text):
#     for receiver, name in receiver_list:
#         try:
#             requests.post(url, auth=("api", api), data={
#                 "from":"giffgaff 分享 <%s>" % sender,
#                 "to": "%s <%s>" % (name,receiver),
#                 "subject": subject,
#                 "text": text
#             })
#             print "Send successfully."
#         except:
#             print "Error: unable to send email"
#
# # Sendcloud发件模块
url="http://sendcloud.sohu.com/webapi/mail.send.json"

def send_email(receiver_list, subject, text):
    for receiver, name in receiver_list:
        params = {"api_user": "giffgaff", \
            "api_key" : "KVYxzpw5S44nf5e3",\
            "to" : "%s" % receiver, \
            "from" : "giffgaff@yongli1992.com", \
            "fromname" : "giffgaff 分享", \
            "subject" : "%s" % subject, \
            "html": "%s" % text \
        }

        try:
            requests.post(url, files="", data=params)
            print("Send successfully.")
        except:
            print("Error: unable to send email!")
