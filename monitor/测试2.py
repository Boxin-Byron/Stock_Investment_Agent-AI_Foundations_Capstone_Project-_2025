import re
import json

data_dict = {'task_id': 'a1b38d7a-2d3d-4da4-a7e0-527f60c336c9', 'workflow_run_id': '1d249954-076f-4dd9-bb03-0560abe7b4b4', 'data': {'id': '1d249954-076f-4dd9-bb03-0560abe7b4b4', 'workflow_id': '93fc2d2c-8ba6-4010-a9d7-42493eb205a7', 'status': 'succeeded', 'outputs': {'text': '```json\n{\n  "sentiment_score": -0.20,\n  "key_events": [\n    "远信工业股价下跌5.01%",\n    "主力资金连续抛售远信工业股票",\n    "远信工业股价波动及交易详情",\n    "远信工业股票行 情及市场表现"\n  ]\n}\n```'}, 'error': '', 'elapsed_time': 11.443518, 'total_tokens': 1305, 'total_steps': 5, 'created_at': 1750748388, 'finished_at': 1750748399}}

    

text = data_dict['data']['outputs']['text'].replace('```json', '').replace('```', '').strip()
text = re.sub(r'\n\s*', '', text)  # 去除换行和多余空格
print(json.loads(text)['key_events'])  # 输出 key_events 列表
