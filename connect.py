import requests


def get_timetable(params: dict) -> dict:
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    paramss = (
        ('dateMonth', f'{params.get("day", "0")}-{params.get("date", "0")}'),
    )

    data = "{" + f'"course":{params.get("course", 3)},"faculty":"{params.get("fac", "FCSA")}","group":"{params.get("group", "1ІСТ-18б")}"' + "}"

    return requests.put('https://jetiq-curriculum-service.herokuapp.com:443/curriculum/byDate', headers=headers,
                        params=paramss, data=data.encode('utf-8')).json()
