# NicoChat

## 概述
NicoChat Interface 是一个基于 Gradio 构建的聊天机器人界面，使用 LLM（大语言模型）来生成对话内容，基于GPT-Sovits或者CosyVoice生成语音(待二次开发)。该项目允许用户与一个名为 NicoNya 的虚拟角色进行互动，您也可以自定义角色卡。

### 注意
当前只支持NicoNya角色，服务商仅支持Ollama、LM_Studio、[siliconflow](https://cloud.siliconflow.cn/)。

## 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/more-nico/NicoChat.git
   cd NicoChat
   ```

2. **安装依赖**
   ```bash
   pip install requests gradio
   ```

3. **配置 API URL 和 API KEY**
   编辑 `user_setting.json` 文件，填写你的配置...

## 使用说明

**启动应用**
   windows在终端下确保python环境OK后，运行`.\main_webui.bat`