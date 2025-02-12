import gradio as gr
import requests
import json

from prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类
from siliconflow_request import SiliconFlowRequest

# Get API_URL and API_KEY from user_setting.json
with open("../user_setting.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    NEW_API_URL = config["API_URL"]
    API_KEY = config["API_KEY"]
def get_formatted_chat(chat_history):
    messages = []
    for message in chat_history:
        if message["role"] == "NicoNya":
            messages.append({"role": "assistant", "content": message['content']})
        elif message["role"] == "morenico":
            messages.append({"role": "user", "content": message['content']})
    return messages

def log_record(log):
    with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
        f.write(f"{log}\n")
# 定义打开和关闭弹窗的回调函数
def open_setting():
    # 更新 modal 和遮罩层为可见
    return gr.update(visible=True), gr.update(visible=True)

def close_setting():
    # 隐藏 modal 和遮罩层
    return gr.update(visible=False), gr.update(visible=False)

def UpdateGR(models, messages):
    return gr.update(choices=models, value="Vendor-A/Qwen/Qwen2.5-72B-Instruct"), gr.update(value=messages)


# 自定义 CSS，用来模拟弹窗和全屏遮罩效果
custom_css = """
#setting-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    z-index: 500;
}
#setting-window {
    position: fixed;
    top: 30%;
    left: 40%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 20px;
    z-index: 1000;
    border: 1px solid rgb(68, 68, 68);
    border-radius: 30px;
    margin: 10%;
    width: 80%;
}
#chatbot {
    min-height: 70vh;
}
#send_btn {
    max-width: 20%;
}
#sending_text {
    min-width: 70%;
}
/* 手机端的按钮样式 */
@media screen and (max-width: 768px) {
    .gr-row { 
        flex-wrap: nowrap !important;  /* 强制单行排列 */
        overflow-x: auto !important;     /* 允许横向滚动 */
    }
    .gr-row > .gr-button { 
        min-width: 50px !important;      /* 压缩按钮最小宽度 */
    }
}
"""

def get_list(api_url):
    response = requests.get(api_url + "api/tags")
    response_dict = json.loads(response.text)
    models = [model["name"] for model in response_dict["models"]]
    for idx, name in enumerate(models, start=1):
        print(f"{idx}. {name}")
    return models
def generate_response(api_url, message, model, top_k, top_p, temperature):
    """
    调用后端 REST API 生成回复，并返回更新后的对话历史。
    此处为同步调用，API 返回 JSON 格式：{ "message": {"content": "生成的回复文本"} }
    """
    llm_request.api_url = api_url
    llm_request.selected_model = model
    llm_request.prompt_gen.json_diag_history.append({"role": "morenico", "content": message})
    formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    yield formatted_chat
    log_record(llm_request.prompt_gen.json_diag_history)
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": llm_request.prompt_gen.FillingPromptGen()}
        ],
        "stream": True,
            "max_tokens": 4096,
            "stop": ["null"],
            "stopping_strings": [
                "\nmorenico:",
                "morenico:",
                "\n**morenico:",
                "\n\n",
                "。\n\n",
                "-\n\n",
                "--\n\n",
                "---\n\n"
            ],
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"},
    }
    log_record("Prompt as follows:")
    log_record(f"{data}\n")
    
    res = ""
    llm_request.prompt_gen.json_diag_history.append({"role": "NicoNya", "content": ""})
    result = ""
    for partial_response in llm_request.get_webui_response(data, data["stopping_strings"]):
        res = partial_response  # 保留最后一次的完整结果
        print(res.rstrip(), end='', flush=True)
        result += res

        # 如果返回中包含 <think 标签，则等待完整结束标签出现后处理
        if "<think" in result:
            if "</think>\n\n" in result:
                # 去除 <think> ... </think> 部分之前的内容
                result = result.split("</think>")[1].strip()
        else:
            # 如果检测到停止字符串，则结束生成
            if data["stopping_strings"] and any(stop_string in result for stop_string in data["stopping_strings"]):
                detected_stop_string = next(
                    (stop_string for stop_string in data["stopping_strings"] if stop_string in result),
                    None
                )
                print(f"检测到停止字符串 \"{detected_stop_string}\"，停止生成。\n")
                result = result.replace(detected_stop_string, "")
                
                if "<think" in result:
                    if "</think>\n\n" in result:
                        # 去除 <think> ... </think> 部分之前的内容
                        result = result.split("</think>")[1].strip()
                        
                llm_request.prompt_gen.json_diag_history[-1] = {"role": "NicoNya", "content": result.rstrip()}
                
                # 格式化聊天历史为消息气泡
                formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
                yield formatted_chat
                break
            
        # # 每次收到新内容后，都yield当前累计的结果
        llm_request.prompt_gen.json_diag_history[-1] = {"role": "NicoNya", "content": result.rstrip()}
        
        # 格式化聊天历史为消息气泡
        formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
        yield formatted_chat

def chat_clean():
    llm_request.prompt_gen = PromptGenerator(CharacterCard("NicoNya"), UserCard("morenico"))
    llm_request.prompt_gen.json_diag_history = [{"role": "NicoNya", "content": llm_request.prompt_gen.CharacterCard.CharacterGreeting}]
    return get_formatted_chat(llm_request.prompt_gen.json_diag_history)

def retry_last(api_url, history, model, top_k, top_p, temperature):
    """
    重试最后一次生成。
    如果历史记录中最后一条为用户消息（即没有对应的回复），则重新调用生成函数；
    如果最后一条为助手回复，则取倒数第二条用户消息重新生成回复，并删除原来的回复。
    """
    print(llm_request.prompt_gen.json_diag_history)
    if not llm_request.prompt_gen.json_diag_history:
        return llm_request.prompt_gen.json_diag_history
    # 判断历史记录长度：若为奇数，最后一条为角色消息；若为偶数，最后一条为用户回复
    if len(llm_request.prompt_gen.json_diag_history) % 2 == 1:
        last_user_msg = llm_request.prompt_gen.json_diag_history[-2]["content"]
        # 去除最后未回复的用户消息
        llm_request.prompt_gen.json_diag_history = llm_request.prompt_gen.json_diag_history[:-2]
    else:
        last_user_msg = llm_request.prompt_gen.json_diag_history[-1]["content"]
        # 去除最后一对用户消息及其回复
        llm_request.prompt_gen.json_diag_history = llm_request.prompt_gen.json_diag_history[:-1]
    
    yield get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    # 重新生成回复
    for partial_response in generate_response(api_url, last_user_msg, model, top_k, top_p, temperature):
        yield partial_response

with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# Nico☆Chat with NicoNya")
        
    llm_request = SiliconFlowRequest(NEW_API_URL, API_KEY)
    try:
        models = llm_request.get_list()
    except:
        raise Exception("Get ModelList Failed, API_URL or API_KEY is wrong")
    
    
    with gr.Row():
        model_select  = gr.Dropdown(label="Select Model", choices=models, value="Vendor-A/Qwen/Qwen2.5-72B-Instruct")
    
    # 使用 gr.Chatbot 组件，type 参数设置为 "messages"，以采用 {'role':..., 'content':...} 格式
    chatbot = gr.Chatbot(value=chat_clean(), type="messages", render_markdown=False, elem_id="chatbot")
    
    with gr.Row():
        txt = gr.Textbox(placeholder="请输入消息", show_label=False, elem_id="sending_text")
        send_btn = gr.Button("发送", elem_id="send_btn")
    
    with gr.Row():
        retry_btn = gr.Button("重试")
        clear_btn = gr.Button("清空聊天")
        btn_settings = gr.Button("设置")
    
    ########## Setting UI ##########
    # 模拟的遮罩层，初始状态为隐藏
    setting_overlay = gr.Column(visible=False, elem_id="setting-overlay")
    
    # 模拟的弹窗容器，初始状态为隐藏
    setting_window = gr.Column(visible=False, elem_id="setting-window")
    
    with setting_window:
        gr.Markdown("### 模型参数设置")
        api_url_input = gr.Textbox(label="API URL", value=NEW_API_URL)
        api_key_input = gr.Textbox(label="API KEY", value=API_KEY)
        top_k = gr.Slider(0, 100, step=1, label="top_k", value=40, info="影响生成多样性，值越大答案越多样")
        top_p = gr.Slider(0.0, 1.0, step=0.05, label="top_p", value=0.9, info="与 top_k 联合控制生成概率分布")
        temperature = gr.Slider(0.0, 2.0, step=0.1, label="temperature", value=0.4, info="温度越高回答越随机")
        btn_close = gr.Button("关闭设置")
    
    # 发送按钮：调用 generate_response 函数，更新聊天历史（chatbot 的值即为对话记录）
    send_btn.click(
        generate_response,
        inputs=[api_url_input, txt, model_select, top_k, top_p, temperature],
        outputs=chatbot
    ).then(
        lambda: "", None, txt  # 发送后清空输入框
    )
    
    txt.submit(
        generate_response,
        inputs=[api_url_input, txt, model_select, top_k, top_p, temperature],
        outputs=chatbot
    ).then(
        lambda: "", None, txt  # 发送后清空输入框
    )
    
    # 清空聊天：直接将对话历史置为空列表
    clear_btn.click(chat_clean, outputs=chatbot)
    
    # 重试按钮：重试最后一次生成
    retry_btn.click(
        retry_last,
        inputs=[api_url_input, chatbot, model_select, top_k, top_p, temperature],
        outputs=chatbot
    )
    
    # 点击“设置”按钮时，显示弹窗和遮罩层
    btn_settings.click(fn=open_setting, inputs=None, outputs=[setting_window, setting_overlay])
    # 点击“关闭设置”按钮时，隐藏弹窗和遮罩层
    btn_close.click(fn=close_setting, inputs=None, outputs=[setting_window, setting_overlay])
    
demo.launch()
