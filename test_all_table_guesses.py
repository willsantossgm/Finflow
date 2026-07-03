import requests

login_url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/auth/v1/token?grant_type=password"
headers = {
    "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
    "Authorization": "Bearer sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
    "Content-Type": "application/json"
}
payload = {"email": "test1@finflow.com", "password": "password123"}

guesses = [
    "gastos", "transacoes", "lancamentos", "lançamentos", "receitas", "despesas", 
    "finflow", "tb_gastos", "transactions", "expenses", "incomes"
]

try:
    response = requests.post(login_url, headers=headers, json=payload)
    data = response.json()
    access_token = data.get("access_token")
    user_id = data.get("user", {}).get("id")
    
    auth_headers = {
        "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    for g in guesses:
        url = f"https://ojiutbtyaxmpwstgnmnn.supabase.co/rest/v1/{g}?limit=1"
        res = requests.get(url, headers=auth_headers)
        print(f"Guess '{g}': status={res.status_code}")
        if res.status_code != 404:
            print(f"SUCCESS/FOUND: '{g}' - response: {res.text[:200]}")
except Exception as e:
    print("Error:", e)
