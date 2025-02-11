import gradio as gr
from prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类
from llm_request import LLMRequest

# 初始化LLMRequest对象
llm_request = LLMRequest(api_url="http://192.168.31.229:11434/")

# 获取模型列表
models = llm_request.get_list()

def get_formatted_chat(chat_history):
    formatted_chat = ""
    for message in chat_history:
        if message["role"] == "NicoNya":
            formatted_chat += f"<div style='text-align: left; margin-right: 50%;'><strong>NicoNya:</strong> {message['content']}</div><br>"
        elif message["role"] == "morenico":
            formatted_chat += f"<div style='text-align: right; margin-left: 50%;'><strong>morenico:</strong> {message['content']}</div><br>"
    return formatted_chat


def log_record(log):
    with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
        f.write(f"{log}\n")
# 定义聊天界面的布局
def chat_interface(api_url, selected_model, user_input, retry_flag):
    llm_request.api_url = api_url
    llm_request.selected_model = selected_model
    
    if retry_flag == "1" and llm_request.prompt_gen.json_diag_history:
        llm_request.prompt_gen.json_diag_history.pop()
        llm_request.prompt_gen.json_diag_history.pop()
        print(llm_request.prompt_gen.json_diag_history)
        formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
        yield formatted_chat
        # return 0
    
    llm_request.prompt_gen.json_diag_history.append({"role": "morenico", "content": user_input})
    print(f"NicoNya: ", end='', flush=True)
    
    # 格式化聊天历史为消息气泡
    formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    yield formatted_chat
    log_record(llm_request.prompt_gen.json_diag_history)
    
    data = {
        "model": selected_model,
        "prompt": llm_request.prompt_gen.FillingPromptGen(),
        "stream": True,
        "max_new_tokens": 350,
        "max_tokens": 350,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "typical_p": 1,
        "typical": 1,
        "sampler_seed": -1,
        "min_p": 0,
        "repetition_penalty": 3,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "skew": 0,
        "min_tokens": 0,
        "add_bos_token": True,
        "smoothing_factor": 0,
        "smoothing_curve": 1,
        "dry_allowed_length": 2,
        "dry_multiplier": 0,
        "dry_base": 1.75,
        "dry_sequence_breakers": [
            "\n",
            ":",
            "\"",
            "*"
        ],
        "dry_penalty_last_n": 0,
        "max_tokens_second": 0,
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
        "stop": [
            "\nmorenico:",
            "morenico:",
            "\n**morenico:",
            "\n\n",
            "。\n\n",
            "-\n\n",
            "--\n\n",
            "---\n\n"
        ],
        "truncation_length": 32768,
        "ban_eos_token": False,
        "skip_special_tokens": True,
        "top_a": 0,
        "tfs": 1,
        "mirostat_mode": 0,
        "mirostat_tau": 5,
        "mirostat_eta": 0.1,
        "custom_token_bans": "",
        "banned_strings": [],
        "xtc_threshold": 0.1,
        "xtc_probability": 0,
        "rep_pen": 1.1,
        "rep_pen_range": 0,
        "repetition_penalty_range": 0,
        "seed": -1,
        "guidance_scale": 1,
        "negative_prompt": "",
        "grammar_string": "",
        "repeat_penalty": 1.1,
        "tfs_z": 1,
        "repeat_last_n": 0,
        "n_predict": 350,
        "num_predict": 350,
        "num_ctx": 8192,
        "mirostat": 0,
        "ignore_eos": False,
        "rep_pen_slope": 1,
        "logit_bias": [],
        "grammar": "",
        "cache_prompt": True
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

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# NicoNya Chat Interface")
    
    with gr.Row():
        api_url_input = gr.Textbox(label="API URL", value="http://192.168.31.229:11434/")
        model_select = gr.Dropdown(label="Select Model", choices=models, value=models[0])
    
    user_input = gr.Textbox(label="User Input")
    confirm_button  = gr.Button("Send")
    retry_button    = gr.Button("Retry")
    
    llm_request.prompt_gen = PromptGenerator(CharacterCard("NicoNya"), UserCard("morenico"))
    
    llm_request.prompt_gen.json_diag_history = [{"role": "NicoNya", "content": llm_request.prompt_gen.CharacterCard.CharacterGreeting}]
    formatted_chat = get_formatted_chat(llm_request.prompt_gen.json_diag_history)
    
    chat_history_display = gr.HTML(label="Chat History", value=formatted_chat)
    
    hidden_retry_confirm = gr.Textbox(value="0", visible=False)
    hidden_retry_retry   = gr.Textbox(value="1", visible=False)

    confirm_button.click(
        fn=chat_interface,
        inputs=[api_url_input, model_select, user_input, hidden_retry_confirm],
        outputs=chat_history_display
    )

    retry_button.click(
        fn=chat_interface,
        inputs=[api_url_input, model_select, user_input, hidden_retry_retry],
        outputs=chat_history_display
    )
demo.launch()