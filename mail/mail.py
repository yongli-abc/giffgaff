# --*-- coding:utf8 --*--
import requests

url = "https://api.mailgun.net/v2/sandboxca42fed017ca4ec7ae250e36e7560562.mailgun.org/messages"
api = "key-3d46b25039688ecfd3c36dd68e660395"
sender = "spread_giffgaff@yongli1992.com"

def send_email(receiver_list, subject, text):
    for receiver, name in receiver_list:
        try:
            requests.post(url, auth=("api", api), data={
                "from":"giffgaff 分享 <%s>" % sender,
                "to": "%s <%s>" % (name,receiver),
                "subject": subject,
                "text": text
            })
            print "Send successfully."
        except:
            print "Error: unable to send email"
