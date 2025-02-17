import gradio as gr
import requests
import json

from ChatLib.prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类
from ChatLib.ollama_request import OllamaLLMRequest
from ChatLib.lm_studio_request import LMStudioLLMRequest
from ChatLib.siliconflow_request import SilliconFlowLLMRequest

from ChatLib.voice_request import get_voice, get_voice_stream
import time


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
    padding: 20px;
    z-index: 1000;
    border: 1px solid rgb(68, 68, 68);
    border-radius: 30px;
    margin: 10%;
    width: 80%;
    max-height: 80vh;
    overflow-y: auto;
}
@media (prefers-color-scheme: dark) {
    #setting-window {
        background: var(--block-border-color); /* 深色模式下的背景颜色 */
    }
}
@media (prefers-color-scheme: light) {
    #setting-window {
        background: var(--block-border-color); /* 浅色模式下的背景颜色 */
    }
}
#setting-params{
    max-height: 50vh;
    display: list-item;
    overflow: overlay;
}
#chatbot {
    min-height: 50vh;
}
#func_btn{
    max-width: 50px;
    border-radius: 20px;
    font-size: 20px;
    padding-left: 0px;
    padding-right: 0px;
    min-width: 20px;
}
#func_btn_block{
    align-items: center;
}
#sending_text {
    min-width: 70%;
}
/*
#audio_blk {
    scale: 1;
}
*/
/* 手机端的按钮样式 */
@media screen and (max-width: 768px) {
    .gr-row { 
        flex-wrap: nowrap !important;  /* 强制单行排列 */
        overflow-x: auto !important;     /* 允许横向滚动 */
    }
    .gr-row > .gr-button { 
        min-width: 30px !important;      /* 压缩按钮最小宽度 */
    }
}
.footer {
    display: none;
}
"""

# Get API_URL and API_KEY from user_setting.json
with open("./user_setting.json", "r", encoding="utf-8") as f:
    setting_json = json.load(f)
    DEFAULT_SERVER  = setting_json["DEFAULT_SERVER"]
    SERVER_LIST     = setting_json["SERVER_LIST"]
    REQUEST_DATA    = setting_json["REQUEST_DATA"]
    VOICE_SERVER    = setting_json["VOICE_SERVER"]

    print(SERVER_LIST)
    
    for server in SERVER_LIST:
        if server["SERVER"] == DEFAULT_SERVER:    config = server

    SERVER  = config["SERVER"]
    API_URL = config["API_URL"]
    API_KEY = config["API_KEY"]
    MODEL   = config["MODEL"]

    CHARACTER_NAME  = setting_json["CHARACTER_NAME"]
    USER_NAME       = setting_json["USER_NAME"]

def get_formatted_chat(chat_history):
    messages = []
    for message in chat_history:
        if message["role"] == CHARACTER_NAME:
            messages.append({"role": "assistant", "content": message['content']})
        elif message["role"] == USER_NAME:
            messages.append({"role": "user", "content": message['content']})
    return messages

def get_formatted_llm_hostory(chat_history):
    messages = []
    for message in chat_history:
        if message["role"] == "assistant":
            messages.append({"role": CHARACTER_NAME, "content": message['content']})
            log_record("TransLatedOK!!!")
        elif message["role"] == "user":
            messages.append({"role": USER_NAME, "content": message['content']})
    return messages

def log_record(log):
    with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
        f.write(f"{log}\n")
def get_list(api_url):
    response = requests.get(api_url + "api/tags")
    response_dict = json.loads(response.text)
    models = [model["name"] for model in response_dict["models"]]
    for idx, name in enumerate(models, start=1):
        print(f"{idx}. {name}")
    return models
def generate_llm_response(api_url, message, model, top_k, top_p, temperature):
    """
    调用后端 API 生成回复，并返回更新后的对话历史。
    此处为同步调用，API 返回 JSON 格式：{ "message": {"content": "生成的回复文本"} }
    """
    llm_request.api_url         = api_url
    llm_request.selected_model  = model
    llm_request.prompt_gen.json_diag_history.append({"role": USER_NAME, "content": message})
    formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    yield formatted_chat
    log_record("Chat History as follows:")
    log_record(llm_request.prompt_gen.json_diag_history)

    data                = REQUEST_DATA
    data["model"]       = model
    data["messages"]    = llm_request.prompt_gen.FillingPromptGen()

    log_record("Prompt as follows:")
    log_record(f"{data}\n")
    
    res = ""
    llm_request.prompt_gen.json_diag_history.append({"role": CHARACTER_NAME, "content": ""})
    result = ""
    for partial_response in llm_request.get_response(data, data["stopping_strings"], webui=True):
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
                        
                llm_request.prompt_gen.json_diag_history[-1] = {"role": CHARACTER_NAME, "content": result.rstrip()}
        
                # 格式化聊天历史为消息气泡
                formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
                yield formatted_chat
                break
            
        # 每次收到新内容后，都yield当前累计的结果
        if "<think" in result:  llm_request.prompt_gen.json_diag_history[-1] = {"role": CHARACTER_NAME, "content": f"{CHARACTER_NAME}正在动脑筋..."}
        else:                   llm_request.prompt_gen.json_diag_history[-1] = {"role": CHARACTER_NAME, "content": result.rstrip()}
        
        # 格式化聊天历史为消息气泡
        formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
        yield formatted_chat
def retry_last(api_url, history, model, top_k, top_p, temperature):
    """
    重试最后一次生成。
    如果历史记录中最后一条为用户消息（即没有对应的回复），则重新调用生成函数；
    如果最后一条为助手回复，则取倒数第二条用户消息重新生成回复，并删除原来的回复。
    """
    print(llm_request.prompt_gen.json_diag_history)
    if not llm_request.prompt_gen.json_diag_history:
        return llm_request.prompt_gen.json_diag_history
    
    if len(llm_request.prompt_gen.json_diag_history)>1:
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
    for partial_response in generate_llm_response(api_url, last_user_msg, model, top_k, top_p, temperature):
        yield partial_response

def revoke_user_chat(api_url, history, model, top_k, top_p, temperature):
    """
    撤回用户的最后一次对话
    """
    print(llm_request.prompt_gen.json_diag_history)
    if not llm_request.prompt_gen.json_diag_history:
        return llm_request.prompt_gen.json_diag_history
    if len(llm_request.prompt_gen.json_diag_history)>1:
        # 判断历史记录长度：若为奇数，最后一条为角色消息；若为偶数，最后一条为用户回复
        if len(llm_request.prompt_gen.json_diag_history) % 2 == 1:
            # 去除最后未回复的用户消息
            llm_request.prompt_gen.json_diag_history = llm_request.prompt_gen.json_diag_history[:-2]
        else:
            # 去除最后一对用户消息及其回复
            llm_request.prompt_gen.json_diag_history = llm_request.prompt_gen.json_diag_history[:-1]
    
    yield get_formatted_chat(llm_request.prompt_gen.json_diag_history)

def chat_clean():
    llm_request.prompt_gen = PromptGenerator(CharacterCard(CHARACTER_NAME), UserCard(USER_NAME))
    llm_request.prompt_gen.json_diag_history = [{"role": CHARACTER_NAME, "content": llm_request.prompt_gen.CharacterCard.CharacterGreeting}]
    return get_formatted_chat(llm_request.prompt_gen.json_diag_history)

# 定义打开和关闭弹窗的回调函数
def open_setting():
    # 更新 modal 和遮罩层为可见
    return gr.update(visible=True), gr.update(visible=True)

def close_setting():
    # 隐藏 modal 和遮罩层
    return gr.update(visible=False), gr.update(visible=False), gr.update(value=SERVER), gr.update(value=API_URL), gr.update(value=API_KEY)
def update_server(server_new):
    global SERVER_LIST
    global SERVER  
    global API_URL 
    global API_KEY 
    global MODEL   
    global CHARACTER_NAME
    global USER_NAME     
    global REQUEST_DATA
    global llm_request

    for server in SERVER_LIST:
        if server["SERVER"] == server_new:    config = server

    return gr.update(value=config["API_URL"]), gr.update(value=config["API_KEY"])

def save_restart_setting(server_new, api_url, api_key, model, character_name, user_name, chat_history):
    global SERVER_LIST
    global SERVER  
    global API_URL 
    global API_KEY 
    global MODEL   
    global CHARACTER_NAME
    global USER_NAME     
    global REQUEST_DATA
    global llm_request

    for server in SERVER_LIST:
        if server["SERVER"] == server_new:    config = server

    SERVER  = config["SERVER"]
    API_URL = config["API_URL"]
    API_KEY = config["API_KEY"]
    MODEL   = config["MODEL"]

    CHARACTER_NAME  = setting_json["CHARACTER_NAME"]
    USER_NAME       = setting_json["USER_NAME"]
    
    if SERVER=="SiliconFlow":   llm_request = SilliconFlowLLMRequest(API_URL, API_KEY)
    elif SERVER=="Ollama":      llm_request = OllamaLLMRequest(API_URL)
    elif SERVER=="LMStudio":    llm_request = LMStudioLLMRequest(API_URL)
    llm_request.prompt_gen = PromptGenerator(CharacterCard(CHARACTER_NAME), UserCard(USER_NAME))
    llm_request.prompt_gen.json_diag_history = get_formatted_llm_hostory(chat_history)

    return gr.update(visible=True), gr.update(visible=True), gr.update(choices=llm_request.get_list(), value=MODEL)

def load_voice(chat_history):
    if VOICE_SERVER!="":
        voice_path = get_voice(CHARACTER_NAME, chat_history[-1]["content"], voice_server=VOICE_SERVER)
        print(voice_path)
        return gr.update(value=voice_path, autoplay=True)

def load_voice_stream(chat_history):
    if VOICE_SERVER!="":
        for partial_response in get_voice_stream(CHARACTER_NAME, chat_history[-1]["content"], voice_server=VOICE_SERVER):
            print(f"WaveFilePath: {partial_response[0]} WaveTime: {partial_response[1]}s")
            with open(partial_response[0], "rb") as f:
                print(len(f.read()))
            yield gr.update(value=partial_response[0], autoplay=True)
            time.sleep(partial_response[1])

with gr.Blocks(css=custom_css, title="Nico⭐️Chat", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# Nico☆Chat with {CHARACTER_NAME}")

    if SERVER=="SiliconFlow":   llm_request = SilliconFlowLLMRequest(API_URL, API_KEY)
    elif SERVER=="Ollama":      llm_request = OllamaLLMRequest(API_URL)
    elif SERVER=="LMStudio":    llm_request = LMStudioLLMRequest(API_URL)
    try:
        models = llm_request.get_list()
    except:
        raise Exception("Get ModelList Failed, API_URL or API_KEY is wrong")
    
    
    with gr.Row():
        model_select  = gr.Dropdown(label="Select Model", choices=models, value=MODEL, show_label=False, container=False)
    
    # 使用 gr.Chatbot 组件，type 参数设置为 "messages"，以采用 {'role':..., 'content':...} 格式
    chatbot = gr.Chatbot(value=chat_clean(), type="messages", render_markdown=False, elem_id="chatbot")
    
    with gr.Row(variant="panel"):
        txt = gr.Textbox(placeholder="请输入消息", show_label=False, elem_id="sending_text", container=False, submit_btn=True)
        # send_btn = gr.Button("发送", elem_id="send_btn")
    
    with gr.Column():
        with gr.Row(elem_id="func_btn_block"):
            voice_btn = gr.Button("🗣️", elem_id="func_btn")
            revoke_btn = gr.Button("↩️", elem_id="func_btn")
            retry_btn = gr.Button("🔁", elem_id="func_btn")
            clear_btn = gr.Button("🧹", elem_id="func_btn")
            btn_settings = gr.Button("⚙", elem_id="func_btn")
        voice_wuhu = gr.Audio(waveform_options=gr.WaveformOptions(show_recording_waveform=False), show_label=False, show_download_button=False, show_share_button=False, scale=0.3, elem_id="audio_blk", visible=False)
    ########## Setting UI ##########
    # 模拟的遮罩层，初始状态为隐藏
    setting_overlay = gr.Column(visible=False, elem_id="setting-overlay")
    
    # 模拟的弹窗容器，初始状态为隐藏
    setting_window = gr.Group(visible=False, elem_id="setting-window")
    
    with setting_window:
        gr.Markdown("### 模型参数设置")

        with gr.Tab("模型参数设置"):
            with gr.Column(elem_id="setting-params"):
                server_input  = gr.Dropdown(label="服务商选择", choices=[item['SERVER'] for item in SERVER_LIST], value=SERVER)
                api_url_input = gr.Textbox(label="API URL", value=API_URL)
                api_key_input = gr.Textbox(label="API KEY", value=API_KEY)
                top_k = gr.Slider(0, 100, step=1, label="top_k", value=40, info="影响生成多样性，值越大答案越多样")
                top_p = gr.Slider(0.0, 1.0, step=0.05, label="top_p", value=0.9, info="与 top_k 联合控制生成概率分布")
                temperature = gr.Slider(0.0, 2.0, step=0.1, label="temperature", value=0.4, info="温度越高回答越随机")
                wuhu01 = gr.Slider(0.0, 2.0, step=0.1, label="wuhu01", value=0.4, info="温度越高回答越随机")
                wuhu02 = gr.Slider(0.0, 2.0, step=0.1, label="wuhu02", value=0.4, info="温度越高回答越随机")
                wuhu03 = gr.Slider(0.0, 2.0, step=0.1, label="wuhu03", value=0.4, info="温度越高回答越随机")
                wuhu04 = gr.Slider(0.0, 2.0, step=0.1, label="wuhu04", value=0.4, info="温度越高回答越随机")
        
        with gr.Tab("芜湖"):
            with gr.Column(elem_id="setting-params"):
                CharacterSel    = gr.Dropdown(label="对话角色选择", choices=["NicoNya"], value="NicoNya")
                UserSel         = gr.Dropdown(label="用户角色选择", choices=["morenico"], value="morenico")
                param_01 = gr.Textbox(label="param_01", value="param_01")
                param_02 = gr.Textbox(label="param_02", value="param_02")
        with gr.Row():
            btn_save_setting    = gr.Button("💾", elem_id="func_btn")
            btn_close_setting   = gr.Button("❌", elem_id="func_btn")
    
    # 发送按钮：调用 generate_llm_response 函数，更新聊天历史（chatbot 的值即为对话记录）
    txt.submit(
        generate_llm_response,
        inputs=[api_url_input, txt, model_select, top_k, top_p, temperature],
        outputs=chatbot
    ).then(
        fn=load_voice_stream,
        inputs=[chatbot],
        outputs=voice_wuhu
    )

    txt.submit(
        lambda : "",
        inputs=None,
        outputs=txt
    )

    voice_btn.click(
        load_voice_stream,
        inputs=chatbot,
        outputs=voice_wuhu
    )
    
    # 清空聊天：直接将对话历史置为空列表
    clear_btn.click(chat_clean, outputs=chatbot)

    revoke_btn.click(
        fn=revoke_user_chat,
        inputs=[api_url_input, chatbot, model_select, top_k, top_p, temperature],
        outputs=chatbot
    )
    
    # 重试按钮：重试最后一次生成
    retry_btn.click(
        retry_last,
        inputs=[api_url_input, chatbot, model_select, top_k, top_p, temperature],
        outputs=chatbot
    ).then(
        fn=load_voice_stream,
        inputs=[chatbot],
        outputs=voice_wuhu
    )

    server_input.change(
        fn=update_server,
        inputs=server_input,
        outputs=[api_url_input, api_key_input]
    )
    
    btn_save_setting.click(
        fn=save_restart_setting,
        inputs=[server_input, api_url_input, api_key_input, model_select, CharacterSel, UserSel, chatbot],
        outputs=[setting_window, setting_overlay, model_select]
    )
    # 点击“设置”按钮时，显示弹窗和遮罩层
    btn_settings.click(fn=open_setting, inputs=None, outputs=[setting_window, setting_overlay])
    # 点击“关闭设置”按钮时，隐藏弹窗和遮罩层
    btn_close_setting.click(
        fn=close_setting, 
        inputs=None, 
        outputs=[setting_window, setting_overlay, server_input, api_url_input, api_key_input]
    )
    
demo.launch(server_name="0.0.0.0")