import requests

try:
    r = requests.post(
        'https://rainstaff.onrender.com/sync/reset',
        headers={'X-Reset-Key': 'rainstaff2026reset'},
        timeout=60
    )
    print('Status:', r.status_code)
    print('Response:', r.text)
except Exception as e:
    print('Error:', e)
