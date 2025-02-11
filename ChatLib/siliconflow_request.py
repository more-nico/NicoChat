import requests
import json
from prompt_gen import PromptGenerator, CharacterCard, UserCard  # 引入PromptGenerator及相关类

# 添加配置变量
NEW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-kwosdhsjwabgalhvoyunroaqxjlznraigpimigptvtrccfxs"

class SiliconFlowRequest:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.models = []
        self.selected_model = None
        self.prompt_gen = None
        self.latest_response = ""
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}",
        }
        
    def get_list(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        querystring = {"type":"text"}
        response = requests.request("GET", "https://api.siliconflow.cn/v1/models", headers=headers, params=querystring)

        print(response.text)

        response_dict = json.loads(response.text)
        self.models = [model["id"] for model in response_dict["data"]]
        for idx, name in enumerate(self.models, start=1):
            print(f"{idx}. {name}")
        return self.models
    def get_response(self, data):
        response = requests.post(self.api_url, json=data, headers=self.headers, stream=True)
        result = ""
        stopping_strings= [
                    "\nmorenico:",
                    "morenico:",
                    "\n**morenico:",
                    "\n\n",
                    "。\n\n",
                    "-\n\n",
                    "--\n\n",
                    "---\n\n"
                    ]
        if response.status_code == 200: 
            with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        f.write(decoded_line + "\n")
                        if decoded_line.startswith("data: ") and "data: [DONE]" not in decoded_line:
                            decoded_line = decoded_line[6:]
                            try:
                                data = json.loads(decoded_line)
                                if data['choices'][0]['delta']['content']==None and data['choices'][0]['delta']['reasoning_content']!=None:
                                    if "\n<think>" not in result:
                                        response_content = "<think>\n"+data['choices'][0]['delta']['reasoning_content']
                                    else:
                                        response_content = data['choices'][0]['delta']['reasoning_content']
                                    result += response_content
                                if data['choices'][0]['delta']['content']!=None and data['choices'][0]['delta']['reasoning_content']==None:
                                    if "<think>" in result and "</think>" not in result:
                                        response_content = "</think>\n"+data['choices'][0]['delta']['content']
                                    else:
                                        response_content = data['choices'][0]['delta']['content']
                                    # result += response_content
                                    # response_content = data['choices'][0]['delta']['content']
                                    result += response_content
                            except json.JSONDecodeError:
                                print(f"Failed to decode JSON: {decoded_line}")
                        print(response_content, end='', flush=True)  # 流式打印输出
                        if ("<think" in result):
                            if "</think>\n\n" in result:
                                result = result.split("</think>")[1].strip()
                        else:
                            if stopping_strings and any(stop_string in result for stop_string in stopping_strings):
                                print(result)
                                f.write("检测到停止字符串，停止生成。" + "\n")
                                break
                return result
            
    def get_webui_response(self, data, stop_strings=None):
        print(self.api_url)
        print(self.headers)
        response = requests.post(self.api_url, json=data, headers=self.headers, stream=True)
        
        result = ""
        think_flag = False
        if response.status_code == 200: 
            with open("output.log", "a", encoding="utf-8") as f:  # 将输出写入文件
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        f.write(decoded_line + "\n")
                        if decoded_line.startswith("data: ") and "data: [DONE]" not in decoded_line:
                            decoded_line = decoded_line[6:]
                            try:
                                data = json.loads(decoded_line)
                                if data['choices'][0]['delta']['content']==None and data['choices'][0]['delta']['reasoning_content']!=None:
                                    if "\n<think>" not in result:
                                        response_content = "<think>\n"+data['choices'][0]['delta']['reasoning_content']
                                    else:
                                        response_content = data['choices'][0]['delta']['reasoning_content']
                                    result += response_content
                                if data['choices'][0]['delta']['content']!=None and data['choices'][0]['delta']['reasoning_content']==None:
                                    if "<think>" in result and "</think>" not in result:
                                        response_content = "</think>\n"+data['choices'][0]['delta']['content']
                                    else:
                                        response_content = data['choices'][0]['delta']['content']
                                    result += response_content
                            except json.JSONDecodeError:
                                print(f"Failed to decode JSON: {decoded_line}")
                        # print(response_content, end='', flush=True)  # 流式打印输出
                        yield response_content

def main():
    llm_request = SiliconFlowRequest(NEW_API_URL, API_KEY)
    # 创建CharacterCard和UserCard实例
    llm_request.prompt_gen = PromptGenerator(CharacterCard("NicoNya"), UserCard("morenico"))
    llm_request.prompt_gen.json_diag_history = [{"role": "NicoNya", "content": llm_request.prompt_gen.CharacterCard.CharacterGreeting}]
    print(f"NicoNya: {llm_request.prompt_gen.CharacterCard.CharacterGreeting}")
    llm_request.get_list()
    while True:
        user_input = input("morenico: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        llm_request.prompt_gen.json_diag_history.append({"role": "morenico", "content": user_input})
        llm_request.get_list()
        # 使用生成的prompt
        data = {
            "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            # "model": "01-ai/Yi-1.5-34B-Chat-16K",
            # "model": "deepseek-ai/DeepSeek-R1",
            # "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
            "messages": [
                {"role": "user", "content": llm_request.prompt_gen.FillingPromptGen()}
            ],
            "stream": True,
            "max_tokens": 4096,
            "stop": ["null"],
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"},
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {API_KEY}",
        }
        print(f"NicoNya: ", end='', flush=True)
        llm_request.prompt_gen.json_diag_history.append({"role": "NicoNya", "content": ""})
        # res = llm_request.get_response(data)
        # llm_request.prompt_gen.json_diag_history[-1] = {"role": "NicoNya", "content": res.rstrip()}
        # print("\n"+"*"*80+"\n"+llm_request.prompt_gen.DiagHistory+"\n"+"*"*80+"\n")
        
        
        for partial_response in llm_request.get_webui_response(data):
            res = partial_response  # 保留最后一次的完整结果
            print(res.rstrip(), end='', flush=True)

if __name__ == "__main__":
    main()
    

