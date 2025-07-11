import requests

url = "http://20.244.56.144/evaluation-service/auth"

payload = {
    "email": "avulakuntasathi@gmail.com",
    "name": "avulakunta sathish kumar",
    "rollNo": "22691a05j9",
    "accessCode": "caVvNH",
    "clientID": "8c5f0645-9c95-4835-b444-87447fc8eb50",
    "clientSecret": "qrzqCzfjtyAsDQdd"
}

response = requests.post(url, json=payload)

print("Response Status:", response.status_code)
print("Response Body:", response.json())