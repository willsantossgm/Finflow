import requests

# 1. Login to get access token
login_url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/token?grant_type=password"
headers = {
    "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
    "Authorization": "Bearer sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
    "Content-Type": "application/json"
}
payload = {"email": "test1@finflow.com", "password": "password123"}

try:
    response = requests.post(login_url, headers=headers, json=payload)
    data = response.json()
    access_token = data.get("access_token")
    
    # 2. Get the PostgREST root with JWT authorization
    root_url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/rest/v1/"
    auth_headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    res = requests.get(root_url, headers=auth_headers)
    print("Status Code:", res.status_code)
    if res.status_code == 200:
        spec = res.json()
        paths = spec.get("paths", {})
        print("Available tables/endpoints in PostgREST:")
        for path in paths.keys():
            print("Endpoint:", path)
    else:
        print("Error response:", res.text)
except Exception as e:
    print("Error:", e)
