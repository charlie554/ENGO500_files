import json
import requests
url='http://pg-api.sensorup.com/st-playground/proxy/v1.0/Datastreams(1115)/Observations'
headers= {
	"Content-Type":"application/json",
	"St-P-Access-Token":"2c0fd43e-8471-4139-a86b-be5e32d7d732",
	}
payload = {"result":3}
print(payload)
r=requests.post(url, data=json.dumps(payload), headers=headers)
print(r)
print(r.text)
