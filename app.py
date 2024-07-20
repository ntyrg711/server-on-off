from flask import Flask, render_template, request, redirect, url_for
import time
import hashlib
import hmac
import base64
import uuid
import requests

# クライアントシークレットをbytes方に変更
def make_secret(secret_key):
    secret_key = bytes(secret_key, 'utf-8')
    return secret_key

# signを作成
def make_sign(secret_key, t, nonce):
    string_to_sign = '{}{}{}'.format(token, t, nonce)
    string_to_sign = bytes(string_to_sign, 'utf-8')
    sign = base64.b64encode(hmac.new(secret_key, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    return sign

# tを作成
def make_t():
    t = int(round(time.time() * 1000))
    return str(t)

# nonceを作成
def make_nonce():
    nonce = str(uuid.uuid4())
    return nonce

app = Flask(__name__)
content = ""
# SwitchBotアプリから取得
secret = "41bfed478a93a262cbd8cb9bb9832f68"
token = "b7206a73a308c7f96aaea78396f739f1d81cbb90d3505ef7db54b33321fba09ba74f132f0ff0b130aa4184ec4561c3f1"
device_id = "DCDA0CDC5EC2"

def make_headers():
    global secret
    global token

    # 必要なパラメータを作成する
    secret_key = make_secret(secret)
    t = make_t()
    nonce = make_nonce()
    sign = make_sign(secret_key, t, nonce)

    # API header作成
    headers = {
        "Authorization": token,
        "sign": sign,
        "t": t,
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf-8"
    }
    return headers

# URL指定
url = "https://api.switch-bot.com/v1.1/devices/{}/status".format(device_id)

@app.route("/")
def index():
    global url
    global content

    headers = make_headers()

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["body"]["power"] == "on":
            status = "on"
        elif data["body"]["power"] == "off":
            status = "off"
        else:
            status = "unknown"
    else:
        status = "unknown(status_code isn't 200)" + str(response.status_code)
    return render_template('index.html', txt=content, status=status)

@app.route("/", methods=['POST'])
def result():
    global content
    global url
    global device_id

    headers = make_headers()

    # リクエストのレスポンス処理（jsonへの変更とデータ型の指定）
    def get_value():
        global url
        global headers
        global content
        global status

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status = data["body"]["power"]
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            if status == "on":
                updated_status = send_command("turnOff")
                content = f"{current_time} : デバイスを正常にオフにしました。"
                status = "off"
            elif status == "off":
                updated_status = send_command("turnOn")
                content = f"{current_time} : デバイスを正常にオンにしました。"
                status = "on"
            return content
        else:
            return

    def send_command(command):
        global device_id
        global headers
        global content

        url = f"https://api.switch-bot.com/v1.1/devices/{device_id}/commands"

        body = {
            "command": command,
            "parameter": "default",
            "commandType": "command"
        }

        response = requests.post(url, headers=headers, json=body)
        content = f"Sending {command}"
        time.sleep(5)
        return
    
    get_value()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
