import requests

url = "http://20.244.56.144/evaluation-service/register"

payload = {
    "email": "avulakuntasathi@gmail.com",                   # 🔁 replace with your email
    "name": "AVULAKUNTA SATHISH KUMAR",                                 # 🔁 your name
    "mobileNo": "9704183308",                            # ✅ add your 10-digit phone number
    "githubUsername": "sathishkumar-08",            # ✅ add your actual GitHub username
    "rollNo": "22691A05J9",                                 # 🔁 your roll number
    "accessCode": "caVvNH",                    # 🔁 from AffordMed email
    "githubRepo": "https://github.com/sathishkumar-08/22691A05J9"  # 🔁 your GitHub repo link
}

response = requests.post(url, json=payload)

print("Response Status:", response.status_code)
print("Response Body:", response.json())
