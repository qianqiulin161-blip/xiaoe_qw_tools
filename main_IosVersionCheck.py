import jwt
import datetime
import requests
from common.robot_api import robot_smallCar
from common.RedisConfig import r


def make_api_request():
    app_id = "6446166926"
    key_id = "924Y3WCXV4"
    issuer_id = "b6efcdb9-089a-4cbc-91d7-ba2a1abb4814"
    private_key = """-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgDCqDIYYe1fBpLow3
StRi6inAHFW1VTUHROeQ2Cy6SJqgCgYIKoZIzj0DAQehRANCAATsl0vUUcu4fzFn
SNgBot1bERbWeXovYqdEFAMH61g1Y0vepM3caCsE0MJO3mi3o33y8e8h5eKPlf4F
u2P6xdqW
-----END PRIVATE KEY-----"""

    # 生成JWT令牌（有效期20分钟）
    token = jwt.encode(
        {
            "iss": issuer_id,
            "exp": int((datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp()),
            "aud": "appstoreconnect-v1"
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id}
    )

    print(token)  # 用于后续API请求的认证

    url = f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/appStoreVersions"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    # 提取版本号
    if "data" in data and len(data["data"]) > 0:
        current_version = data["data"][0]["attributes"]["versionString"]
        print(f"当前版本: {current_version} {type(current_version)}")
        return current_version
    else:
        print("获取失败:", data)
        return 'False'


if __name__ == '__main__':
    try:
        current_version = make_api_request()
        if current_version != 'False':
            if r.get('IosVersion'):
                if current_version == r.get('IosVersion'):
                    print(f'IOS版本暂无更新')
                else:
                    r.set('IosVersion', current_version)
                    robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": f"🌟🌟小鹅通AppIOS更新啦: {current_version}"
            }
        }, 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=24ede094-cff2-4af1-a9f5-6d9badc05bd3')
            else:
                r.set('IosVersion', current_version)
    except Exception as e:
        print(f"最终请求失败，原因: {e}")
