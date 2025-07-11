import requests

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJhdnVsYWt1bnRhc2F0aGlAZ21haWwuY29tIiwiZXhwIjoxNzUyMjE0MDY5LCJpYXQiOjE3NTIyMTMxNjksImlzcyI6IkFmZm9yZCBNZWRpY2FsIFRlY2hub2xvZ2llcyBQcml2YXRlIExpbWl0ZWQiLCJqdGkiOiIwNTU5NmYzYi1jNGJlLTQwNWItOWRhMi01NWEwMjY3MzUwOTkiLCJsb2NhbGUiOiJlbi1JTiIsIm5hbWUiOiJhdnVsYWt1bnRhIHNhdGhpc2gga3VtYXIiLCJzdWIiOiI4YzVmMDY0NS05Yzk1LTQ4MzUtYjQ0NC04NzQ0N2ZjOGViNTAifSwiZW1haWwiOiJhdnVsYWt1bnRhc2F0aGlAZ21haWwuY29tIiwibmFtZSI6ImF2dWxha3VudGEgc2F0aGlzaCBrdW1hciIsInJvbGxObyI6IjIyNjkxYTA1ajkiLCJhY2Nlc3NDb2RlIjoiY2FWdk5IIiwiY2xpZW50SUQiOiI4YzVmMDY0NS05Yzk1LTQ4MzUtYjQ0NC04NzQ0N2ZjOGViNTAiLCJjbGllbnRTZWNyZXQiOiJxcnpxQ3pmanR5QXNEUWRkIn0.smzbsSgm3uzokwHCodUMNPicgUSorFTVcK5TAypFf98"  

def log(stack, level, package, message):
    url = "http://20.244.56.144/evaluation-service/logs"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("Log:", response.status_code, response.json())
    except Exception as e:
        print("Logging failed:", e)
