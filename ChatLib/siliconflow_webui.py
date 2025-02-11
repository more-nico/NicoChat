import gradio as gr
from prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类
from siliconflow_request import SiliconFlowRequest

# 初始化LLMRequest对象
NEW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-kwosdhsjwabgalhvoyunroaqxjlznraigpimigptvtrccfxs"

llm_request = SiliconFlowRequest(NEW_API_URL, API_KEY)

# 获取模型列表
models = llm_request.get_list()

def get_formatted_chat(chat_history):
    formatted_chat = ""
    for message in chat_history:
        if message["role"] == "NicoNya":
            formatted_chat += f"<div style='text-align: left; margin-right: 10%;'><strong>NicoNya:</strong> <br>{message['content']}</div><br>"
        elif message["role"] == "morenico":
            formatted_chat += f"<div style='text-align: right; margin-left: 10%;'><strong>morenico:</strong> <br>{message['content']}</div><br>"
    return formatted_chat

# def get_formatted_chat(chat_history):
#     chat_div_content = ""
#     for message in chat_history:
#         if message["role"] == "NicoNya":
#             chat_div_content += (
#                 f"<div style='text-align: left; margin-right: 10%;'>"
#                 f"<strong>NicoNya:</strong><br>{message['content']}"
#                 "</div><br>"
#             )
#         elif message["role"] == "morenico":
#             chat_div_content += (
#                 f"<div style='text-align: right; margin-left: 10%;'>"
#                 f"<strong>morenico:</strong><br>{message['content']}"
#                 "</div><br>"
#             )
#     # 外层 div，设置最大高度、滚动条，并添加 id
#     formatted_chat = f"""
#     <div id="chat-container" style="max-height: 500px; overflow-y: auto; padding: 10px; border: 1px solid #ccc;">
#         {chat_div_content}
#     </div>
#     <script>
#       // 自动滚动到最底部
#       var chatDiv = document.getElementById("chat-container");
#       chatDiv.scrollTop = chatDiv.scrollHeight;
#     </script>
#     """
#     return formatted_chat



def log_record(log):
    with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
        f.write(f"{log}\n")
# 定义聊天界面的布局
def chat_interface(api_url, selected_model, user_input, retry_flag):
    llm_request.api_url = api_url
    llm_request.selected_model = selected_model
    
    if retry_flag == "1" and llm_request.prompt_gen.json_diag_history:
        llm_request.prompt_gen.json_diag_history.pop()
        # llm_request.prompt_gen.json_diag_history.pop()
        print(llm_request.prompt_gen.json_diag_history)
        formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
        yield formatted_chat
        # return 0
    else:
        llm_request.prompt_gen.json_diag_history.append({"role": "morenico", "content": user_input})
    print(f"NicoNya: ", end='', flush=True)
    
    # 格式化聊天历史为消息气泡
    formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    yield formatted_chat
    log_record(llm_request.prompt_gen.json_diag_history)
    
    data = {
        "model": selected_model,
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
                yield result  # 将最后的结果yield出去
                
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
# 修改confirm_button的点击事件，清空user_input
def on_confirm():
    return ""  # 清空user_input
    
# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# Nico☆Chat with NicoNya")
    
    with gr.Row():
        api_url_input = gr.Textbox(label="API URL", value=NEW_API_URL, visible=False)
        api_key_input = gr.Textbox(label="API KEY", value=API_KEY, visible=False)
        model_select  = gr.Dropdown(label="Select Model", choices=models, value="Vendor-A/Qwen/Qwen2.5-72B-Instruct")
    
    
    formatted_chat = chat_clean()
    chat_history_display = gr.HTML(label="Chat History", value=chat_clean())
    
    user_input = gr.Textbox(label="User Input")
    
    with gr.Row(visible=True) as button_row:  # 添加样式到按钮行
        confirm_button = gr.Button("Send", min_width=50)
        retry_button = gr.Button("Retry", min_width=50)
        clean_button = gr.Button("Clean", min_width=50)

    # 在Blocks中添加CSS样式
    demo.css = """
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
    hidden_retry_confirm = gr.Textbox(value="0", visible=False)
    hidden_retry_retry   = gr.Textbox(value="1", visible=False)
    

    # 添加事件监听器，当按下Enter键时触发confirm_button
    user_input.submit(
        fn=chat_interface,
        inputs=[api_url_input, model_select, user_input, hidden_retry_confirm],
        outputs=chat_history_display
    )
    user_input.submit(
        fn=on_confirm,
        outputs=user_input
    )
    
    confirm_button.click(
        fn=chat_interface,
        inputs=[api_url_input, model_select, user_input, hidden_retry_confirm],
        outputs=chat_history_display
    )
    confirm_button.click(
        fn=on_confirm,
        outputs=user_input
    )

    retry_button.click(
        fn=chat_interface,
        inputs=[api_url_input, model_select, user_input, hidden_retry_retry],
        outputs=chat_history_display
    )
    
    clean_button.click(
        fn=chat_clean,
        outputs=chat_history_display
    )
demo.launch(server_name="0.0.0.0")