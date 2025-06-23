import re
import json

def extract_second_last_data(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 使用正则表达式匹配所有的 data: 结构
    pattern = r'data:\s*(\{.*?\})'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # 检查是否有足够的匹配项
    if len(matches) < 2:
        raise ValueError("文件中没有足够的 'data:' 结构")
    
    # 提取倒数第二个匹配的字典
    second_last_data_str = matches[-2]
    
    # 将字符串转换为字典
    try:
        second_last_data_dict = json.loads(second_last_data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"解析错误: {e}")
    
    return second_last_data_dict

# 假设文件路径为 'data.txt'
file_path = 'data.txt'
second_last_data_dict = extract_second_last_data(file_path)

# 打印提取的字典
print(second_last_data_dict)
    
