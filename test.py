import requests
import json

# load services.json and make a list of the url field
urls = []
json_data = open("services.json")
data = json.load(json_data)
for service in data:
    s = data[service]
    urls.append(s["url"])
json_data.close()
print(urls)


headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/81.0.4044.141 Safari/537.36"}

for url in urls:
    res = requests.head(url, headers=headers, timeout=10)
    print(url, res.status_code)