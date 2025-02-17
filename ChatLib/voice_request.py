import requests
from datetime import datetime
import re
import wave
import threading
import queue

def clean_text(text):
    # 调整后的正则表达式，排除括号、斜线和特殊圆点符号
    pattern = re.compile(
        r'[^\u4e00-\u9fa5'    # 中文字符
        r'\u3040-\u30FF'      # 新增日语字符（平假名、片假名）
        r'a-zA-Z0-9'          # 英文字母和数字
        r'\s'                 # 空格
        r'\u3000-\u303F'      # 中文标点
        r'\uFF01-\uFF1F'      # 全角符号
        r'\u0020-\u0027'      # 基础ASCII
        r'\u002a-\u002e'      # 基础ASCII
        r'\u0030-\u007E'      # 基础ASCII
        r']'
    )
    return pattern.sub('', text)


def split_chinese_sentences(text):
    # 使用正则表达式匹配中文句号、问号、感叹号等标点符号
    pattern = re.compile(r'(?<=[。！？~])')
    sentences = pattern.split(text)
    # 去除空字符串
    sentences = [s.strip() for s in sentences if s.strip()]
    
    merged_sentences = []
    i = 0
    while i < len(sentences):
        current_sentence = sentences[i]
        # 如果当前句子长度小于5且后面还有句子，就与后面的句子合并
        while len(current_sentence) < 5 and i < len(sentences) - 1:
            i += 1
            current_sentence += sentences[i]
        merged_sentences.append(current_sentence)
        i += 1

    return merged_sentences

def get_wav_duration(filename):
    with wave.open(filename, 'r') as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        duration = frames / float(rate)
        return duration
    
def get_voice(CharacterName, chat_str, voice_server="http://192.168.31.102:3050/"):
    # 定义请求的URL
    url = voice_server+"/get_voice"
    try:
        # 发送GET请求
        response = requests.get(
            url,
            params={"chat_str": clean_text(chat_str)}
        )
        # 检查响应状态
        if response.status_code == 200:
            voice_file = f"{CharacterName}_{datetime.now().timestamp()}.wav"
            # 保存音频文件
            with open(f"./Src/Voice/{voice_file}", "wb") as f:
                f.write(response.content)
        else:
            print(f"请求失败，状态码：{response.status_code}")
        return f"./Src/Voice/{voice_file}"

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误发生: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"连接错误发生: {conn_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误发生: {req_err}")
    except ValueError as json_err:
        print(f"JSON解析错误: {json_err}")

def get_voice_stream(CharacterName, chat_str, voice_server="http://192.168.31.102:3050/"):
    # 定义请求的URL
    url = voice_server+"/get_voice"
    chat_str = chat_str.replace(f"{CharacterName}:", "")
    chat_str_splited = split_chinese_sentences(clean_text(chat_str))
    
    # 每次调用创建独立的状态控制
    local_queue = queue.Queue()
    local_processing_complete = False  # 改为局部变量

    def local_producer():
        nonlocal local_processing_complete
        for sentence in chat_str_splited:
            try:
                response = requests.get(
                    url,
                    params={"chat_str": sentence}
                )
                if response.status_code == 200:
                    voice_file = f"{CharacterName}_{datetime.now().timestamp()}.wav"
                    with open(f"./Src/Voice/{voice_file}", "wb") as f:
                        f.write(response.content)
                    local_queue.put([f"./Src/Voice/{voice_file}", 
                                get_wav_duration(f"./Src/Voice/{voice_file}")])
                    # print(f" [队列写入] 当前队列数量：{local_queue.qsize()}")  # 新增写入监控

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP错误发生: {http_err}")
            except requests.exceptions.ConnectionError as conn_err:
                print(f"连接错误发生: {conn_err}")
            except requests.exceptions.RequestException as req_err:
                print(f"请求错误发生: {req_err}")
            except ValueError as json_err:
                print(f"JSON解析错误: {json_err}")
        local_processing_complete = True  # 更新为局部变量

    def local_consumer():
        try:
            while not (local_processing_complete and local_queue.empty()):
                try:
                    item = local_queue.get(timeout=1)
                    # print(f" [队列读取] 剩余数量：{local_queue.qsize()}")  # 新增读取监控
                    if item:
                        yield item
                    local_queue.task_done()
                except queue.Empty:
                    continue
        finally:
            # 清空队列保障逻辑
            with local_queue.mutex:  # 直接操作队列底层数据结构
                local_queue.queue.clear()
            # print("队列已清空")

    # 启动线程时使用新的局部变量
    producer_thread = threading.Thread(target=local_producer)
    producer_thread.start()

    return local_consumer()