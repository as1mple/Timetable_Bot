import requests


def get_response(params: dict) -> dict:
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    data = f'"course":{params.get("course", 3)},"faculty":"{params.get("fac", "FCSA")}","group":"{params.get("group", "1ІСТ-18б")}"'
    data = "{" + data + "}"

    return requests.put('https://jetiq-curriculum-service.herokuapp.com:443/curriculum/convenient', headers=headers,
                        data=data.encode('utf-8')).json()
