from config import client

def chat_with_gpt(messages: list, prompt: str) -> str:
    """
    与 GPT 模型进行对话
    """
    messages.append({"role": "user", "content": prompt})

    # 限制对话轮数，防止 token 超限
    if len(messages) > 10:
        messages = [messages[0]] + messages[-9:]

    response = client.chat.completions.create(
        model = "gpt-4o",
        messages = messages,
        temperature = 0
    )
    
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    return reply

def sql_chat_with_gpt(messages: list, input_prompt: str) -> str:
    """
    与 GPT 模型进行对话(仅用于SQL评估和修正)
    """
    messages.append({"role": "user", "content": input_prompt})
    response = client.chat.completions.create(
        model = "gpt-4o",
        messages = messages,
        temperature = 0
    )
    reply = response.choices[0].message.content
    return reply

#流式对话
def chat_with_gpt_stream(messages: list, prompt: str) -> str:
    """
    与 GPT 模型进行流式对话
    """
    messages.append({"role": "user", "content": prompt})  # 追加用户输入

    response = client.chat.completions.create(
        model = "gpt-4o",
        messages = messages,
        temperature = 0.7,
        stream = True
    )

    reply = ""
    for chunk in response:
        if chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                reply += content

    print("\n")
    messages.append({"role": "assistant", "content": reply})
    return reply

# 测试对话
# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ["exit", "quit"]:
#         print("Goodbye!")
#         break
#     reply = chat_with_gpt(user_input)
#     print("ChatGPT:", reply)

# # 测试流式对话
# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ["exit", "quit"]:
#         print("Goodbye!")
#         break
#     chat_with_gpt_stream(user_input)