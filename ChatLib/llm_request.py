import requests
import json
from prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类

# 添加配置变量
OLLAMA_API_URL = "http://192.168.31.229:11434/"

class LLMRequest:
    def __init__(self, api_url):
        self.api_url = api_url
        self.models = []
        self.selected_model = None
        self.prompt_gen = None
        self.latest_response = ""

    def get_list(self):
        response = requests.get(self.api_url + "api/tags")
        response_dict = json.loads(response.text)
        self.models = [model["name"] for model in response_dict["models"]]
        for idx, name in enumerate(self.models, start=1):
            print(f"{idx}. {name}")
        return self.models
    
    def get_response(self, data, stop_strings=None):
        response = requests.post(self.api_url + "api/generate", json=data, stream=True)  # 使用流式输出
        result = ""
        with open("output.log", "a", encoding="utf-8") as f:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    f.write(decoded_line + "\n")
                    try:
                        json_data = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        continue  # 如果无法解析JSON，则跳过这一行
                    response_content = json_data.get("response", "")
                    print(response_content, end='', flush=True)  # 流式打印输出到控制台
                    result += response_content
                    self.latest_response = response_content  # 更新最新响应内容

                    # 如果返回中包含 <think 标签，则等待完整结束标签出现后处理
                    if "<think" in result:
                        if "</think>\n\n" in result:
                            # 去除 <think> ... </think> 部分之前的内容
                            result = result.split("</think>")[1].strip()
                    else:
                        # 如果检测到停止字符串，则结束生成
                        if stop_strings and any(stop_string in result for stop_string in stop_strings):
                            detected_stop_string = next(
                                (stop_string for stop_string in stop_strings if stop_string in result),
                                None
                            )
                            f.write(f"检测到停止字符串 \"{detected_stop_string}\"，停止生成。\n")
                            result = result.replace(detected_stop_string, "")
                            yield result  # 将最后的结果yield出去
                            break
                    # 每次收到新内容后，都yield当前累计的结果
                    yield result
        print()  # 换行
        
    def get_webui_response(self, data, stop_strings=None):
        response = requests.post(self.api_url + "api/generate", json=data, stream=True)  # 使用流式输出
        result = ""
        with open("output.log", "a", encoding="utf-8") as f:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    f.write(decoded_line + "\n")
                    try:
                        json_data = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        continue  # 如果无法解析JSON，则跳过这一行
                    response_content = json_data.get("response", "")
                    # print(response_content, end='', flush=True)  # 流式打印输出到控制台
                    yield response_content
        print()  # 换行

    def select_model(self, selected_model_idx):
        selected_model_idx = selected_model_idx - 1
        if 0 <= selected_model_idx < len(self.models):
            self.selected_model = self.models[selected_model_idx]
            self.prompt_gen = PromptGenerator(CharacterCard("NicoNya"), UserCard("morenico"))
            self.prompt_gen.DiagHistory = "NicoNya: " + self.prompt_gen.CharacterCard.CharacterGreeting
            self.prompt_gen.json_diag_history = [{"role": "NicoNya", "content": self.prompt_gen.CharacterCard.CharacterGreeting}]
            print(f"NicoNya: {self.prompt_gen.CharacterCard.CharacterGreeting}")
        else:
            print("无效的模型编号")
    def start_chat(self):
        if not self.selected_model:
            print("请先选择一个模型。")
            return

        user_input = input("morenico: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            return False

        # 更新对话历史：用户输入
        self.prompt_gen.DiagHistory += "\nmorenico: " + user_input
        self.prompt_gen.json_diag_history.append({"role": "morenico", "content": user_input})

        data = {
            "model": self.selected_model,
            "prompt": self.prompt_gen.FillingPromptGen(),  # 使用生成的 prompt
            "stream": True,  # 设置为流式输出
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
        print("NicoNya: ", end='', flush=True)
        with open("output.log", "a", encoding="utf-8") as f:
            f.write("Prompt as follows:\n")
            f.write(f"{data}\n")

        # 直接遍历 get_response 返回的生成器，流式输出响应内容
        result = ""
        for partial_response in self.get_response(data, data["stopping_strings"]):
            # 每次 yield 的内容都打印到控制台
            # print(partial_response, end='', flush=True)
            result = partial_response  # 保留最后一次的完整结果
        while input("Need Retry?")=='y':
            for partial_response in self.get_response(data, data["stopping_strings"]):
                # 每次 yield 的内容都打印到控制台
                # print(partial_response, end='', flush=True)
                result = partial_response  # 保留最后一次的完整结果

        # 更新对话历史：机器人回复
        self.prompt_gen.DiagHistory += "\nNicoNya: " + result.rstrip()
        self.prompt_gen.json_diag_history.append({"role": "NicoNya", "content": result.rstrip()})

        print("\n" + "*" * 80 + "\n" + self.prompt_gen.DiagHistory + "\n" + "*" * 80 + "\n")
        return True

def main():
    llm_request = LLMRequest(OLLAMA_API_URL)
    llm_request.get_list()
    llm_request.select_model(int(input("Select Model: ")))
    while llm_request.start_chat():
        pass

if __name__ == "__main__":
    main()