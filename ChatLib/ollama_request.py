import requests
import json
# from ChatLib.prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类
from .prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类

# 添加配置变量
OLLAMA_API_URL = "http://127.0.0.1:11434/"

class OllamaLLMRequest:
    def __init__(self, api_url):
        self.api_url = api_url
        self.models = []
        self.selected_model = None
        self.prompt_gen = None
        self.latest_response = ""

    def get_list(self):
        response = requests.get(self.api_url + "v1/models")
        response_dict = json.loads(response.text)
        self.models = [model["id"] for model in response_dict["data"]]
        for idx, name in enumerate(self.models, start=1):
            print(f"{idx}. {name}")
        return self.models
    
    def get_response(self, data, stop_strings=None, webui=False):
        response = requests.post(self.api_url + "/api/chat", json=data, stream=True)  # 使用流式输出
        result = ""
        with open("output.log", "a", encoding="utf-8") as f:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    f.write(decoded_line + "\n")
                    if decoded_line.startswith("data: ") and "data: [DONE]" not in decoded_line:
                            decoded_line = decoded_line[6:]
                    try:
                        json_data = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        continue  # 如果无法解析JSON，则跳过这一行
                    response_content = json_data.get("message", "").get("content", "")
                    result += response_content
                    self.latest_response = response_content

                    if not webui:
                        if "<think" in result:
                            if "</think>\n\n" in result:
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
                                # if webui:   yield result
                                # else    :   yield "</STOP>"
                                break

                    yield response_content

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
        
        self.prompt_gen.DiagHistory += "\nmorenico: " + user_input
        self.prompt_gen.json_diag_history.append({"role": "morenico", "content": user_input})

        data = {
            "model"             : self.selected_model,
            "messages"          : self.prompt_gen.FillingPromptGen(),
            "stream"            : True,
            "max_tokens"        : 2048,
            "temperature"       : 1.0,
            "top_p"             : 0.7,
            "top_k"             : 50,
            "presence_penalty"  : 1.0,
            "frequency_penalty" : 0.8,
            "stopping_strings"  : [
                "\nmorenico:",
                "morenico:",
                "\n**morenico:",
                "\n\n",
                "。\n\n",
                "-\n\n",
                "--\n\n",
                "---\n\n"
            ]
        }
        print("NicoNya: ", end='', flush=True)
        with open("output.log", "a", encoding="utf-8") as f:
            f.write("Prompt as follows:\n")
            f.write(f"{data}\n")
        print("Prompt as follows:")
        print(data)

        result = ""
        for partial_response in self.get_response(data, data["stopping_strings"]):
            print(partial_response, end='', flush=True)
            result += partial_response  # 保留最后一次的完整结果
        while input("Need Retry?")=='y':
            result = ""
            for partial_response in self.get_response(data, data["stopping_strings"]):
                print(partial_response, end='', flush=True)
                result += partial_response

        if "<think" in result:
            if "</think>\n\n" in result:
                result = result.split("</think>")[1].strip()
        self.prompt_gen.DiagHistory += "\nNicoNya: " + result.rstrip()
        self.prompt_gen.json_diag_history.append({"role": "NicoNya", "content": result.rstrip()})

        print("\n" + "*" * 80 + "\n" + self.prompt_gen.DiagHistory + "\n" + "*" * 80 + "\n")
        return True
def main():
    llm_request = OllamaLLMRequest(OLLAMA_API_URL)
    llm_request.get_list()
    llm_request.select_model(int(input("Select Model: ")))
    while llm_request.start_chat():
        pass

if __name__ == "__main__":
    main()