# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

def get_stock_code_with_deepseek(stock_name: str):
    client = OpenAI(api_key="sk-653829eacd30417996f70834039c0414", base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个股票信息查询助手。"},
            {"role": "user", "content": f"请问{stock_name}的股票代码是什么？只需要告诉我代码即可，不要额外的内容。"},
        ],
        stream=False
    )

    print(response.choices[0].message.content)
    # print(response)
get_stock_code_with_deepseek('苹果')