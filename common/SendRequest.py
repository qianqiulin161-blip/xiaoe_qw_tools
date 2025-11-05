import requests


class SendRequest:
    # 会话，能够自动管理我们的cookie关联
    sess = requests.session()

    @staticmethod
    def all_send_request(method, url, **kwargs):
        res = SendRequest.sess.request(method, url, **kwargs)
        return res
