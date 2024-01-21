import json
import datetime

def timeUpdate():
    with open("services.json", "r") as f:
        j = json.load(f)

    for k in j.keys():
        j[k]["Last access time"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open("services.json", "w") as out:
        json.dump(j, out, indent=4, sort_keys=True, default=str)