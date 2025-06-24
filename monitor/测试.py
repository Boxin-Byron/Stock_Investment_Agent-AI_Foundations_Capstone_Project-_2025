import requests

headers = {
    'Authorization': 'Bearer app-Pmqm52DKmWlzsTi07I3uQbSn',
    'Content-Type': 'application/json',
}

json_data = {
    'inputs': {
        'stock_code': '301053',
    },
    'query': '为我分析这支股票',
    'response_mode': 'blocking',
    'user': 'abc-123',
}
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}
response = requests.post('https://api.dify.ai/v1/chat-messages', headers=headers, json=json_data,proxies=proxies)
print(response.status_code)
print(response.text)


import json
from pprint import pprint


# # 这是您提供的完整字符串
def process_dify_flow_outputs(dify_flow_output):
    input_string = dify_flow_output['answer']
    string = input_string.replace("\n", "")
    str_list = string.split("}{")
    
    # 确保我们有三个独立字典
    str_list[0] += "}"
    str_list[1] = "{" + str_list[1] + "}"
    str_list[2] = "{" + str_list[2]
    
    new_list = []
    for item in str_list:
        try:
            # 直接加载为JSON对象
            parsed_item = json.loads(item)
            
            # 特别处理第一个字典(latest_metrics)
            if 'latest_metrics' in parsed_item:
                try:
                    # 尝试解析latest_metrics字符串
                    if isinstance(parsed_item['latest_metrics'], str):
                        parsed_item['latest_metrics'] = json.loads(parsed_item['latest_metrics'])
                except json.JSONDecodeError:
                    # 如果无法解析，保持原始格式
                    pass
                
            new_list.append(parsed_item)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e} | 原始内容: {item}")
            # 如果无法解析为JSON，作为纯文本存入
            new_list.append({"raw_content": item})
    return new_list

dict_data = response.json()

list_data = process_dify_flow_outputs(dict_data)
for item in list_data:
    print(item)