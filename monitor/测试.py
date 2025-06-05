 
import requests
 
url = "https://api.dify.com/workflows"
headers = {"Authorization": "Bearer app-HWzyDDddmtSZVv5Mi97P9yCw"}
params = {"name": "k线量价分析v0"}
 
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
response = requests.get(url, headers=headers, params=params,proxies=proxies)
if response.status_code == 200:
    data = response.json()
    print(data)
    for workflow in data['workflows']:
        print(f"Workflow ID: {workflow['id']}")
else:
    print("Error fetching workflows:", response.text)