import requests
from requests.structures import CaseInsensitiveDict
import json
from get_proxy import loginproxy


# username = input("Enter the email/name:")
# password = input("Enter the password:")
# thething = requests.get("http://comb.ml:4440/mclogin/", params = {"username": username, "password": password})
# print(json.loads(thething.content))

def login(username, password, clienttoken="none"):
    url = "https://authserver.mojang.com/authenticate"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"


    data = {
        "agent": {
            "name": "Minecraft",
            "version": 1

        },
        "username": username,
        "password": password,
        "clientToken": clienttoken,
        "requestUser": "true"
    }

    data = json.dumps(data)

    # print(data)

    resp = requests.post(url, headers=headers, data=data)

    print(resp.content)
    return json.loads(resp.text)

def seigen_login(user, pswd, clienttoken="none"):
    url = loginproxy() + "?username=" + user + "&password=" + pswd + "&token=" + clienttoken
    req = requests.get(url)
    return json.loads(req.text)

if __name__ == "__main__":
    name=input("Your username/email:")
    pswd=input("Your password will only be sent to mojang:")
    print(login(name, pswd))