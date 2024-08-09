import requests
import json

# res = requests.put("http://localhost:5000/artists/1", params={'hi': 'world'}, json=json.dumps({"Name": "AC/DCB"}))
res = requests.post("http://localhost:5000/artists", json={"Name": "Drake"})
print(res.status_code, res.content)
print(requests.get("http://localhost:5000/artists").json())
