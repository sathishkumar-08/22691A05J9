import requests

url = "http://20.244.56.144/evaluation-service/register"

payload = {
    "email": "avulakuntasathi@gmail.com",                  
    "name": "AVULAKUNTA SATHISH KUMAR",                              
    "mobileNo": "9704183308",                           
    "githubUsername": "sathishkumar-08",            
    "rollNo": "22691A05J9",                                
    "accessCode": "caVvNH",                   
    "githubRepo": "https://github.com/sathishkumar-08/22691A05J9"  
}

response = requests.post(url, json=payload)

print("Response Status:", response.status_code)
print("Response Body:", response.json())
