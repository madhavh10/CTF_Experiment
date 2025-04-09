import requests
import json

url = "http://localhost:8000/api/v1/challenges"

payload = {}
headers = {
  'Authorization': 'Token ctfd_b292ab6c693fc59b76c62c6145b44c4be91bac8b549681c61c2287e46b1d68b8',
  'Content-Type': 'application/json',
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)