# AI Chat System

一个功能丰富的 AI 聊天系统，提供多种界面实现和灵活的配置选项。

## 项目结构

project/
├── stream_chat_app.py # 核心基类，实现基本聊天功能
├── chat_app.py # 简单的Flask聊天实现
├── custom_chat_app.py # 带系统提示词设置的Flask实现
├── gradio_chat_app.py # Gradio界面实现
├── templates/
│ ├── index.html # 基础聊天界面
│ ├── stream_chat.html # 流式响应聊天界面
│ └── custom_chat.html # 自定义系统提示词界面
├── .env # 环境变量配置
└── requirements.txt # 项目依赖

## 核心功能模块

### 基础类 (stream_chat_app.py)

- `ChatMessage`: 消息数据类
- `ChatSession`: 会话管理类
- `StreamChatApp`: 核心应用类
  - 实现了消息处理
  - 会话管理
  - 流式响应
  - API调用

### 三种界面实现

1. **基础Flask界面** (chat_app.py)
   - 简单的聊天功能
   - 基本的消息历史

2. **高级Flask界面** (custom_chat_app.py)
   - 支持系统提示词自定义
   - 流式响应显示
   - 完整的会话管理

3. **Gradio界面** (gradio_chat_app.py)
   - 现代化的UI
   - 系统提示词实时修改
   - 更好的用户体验

## 主要特性

1. **消息处理**
   - 支持流式响应
   - 消息历史管理
   - 错误处理

2. **会话管理**
   - 会话状态保持
   - 历史记录
   - 系统提示词设置

3. **用户界面**
   - 实时响应
   - 打字机效果
   - 清晰的消息展示

4. **系统配置**
   - 环境变量配置
   - 灵活的部署选项
   - 日志记录

## 技术栈

### 后端

- Flask
- OpenAI API
- Python数据类
- 线程锁

### 前端

- HTML/CSS/JavaScript
- Server-Sent Events
- Gradio UI

### 工具

- dotenv
- logging
- dataclasses

## 安装和使用

1. **克隆项目**

   ``` bash
   git clone https://github.com/Namo1999/AI-Chat-System.git
   cd ai-chat-system
   ```

2. **安装依赖**

   ``` bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**

创建 `.env` 文件并配置以下变量：DASHSCOPE_API_KEY=your_api_key_here

4. **运行不同版本**

``` bash
   # 基础版本
   python chat_app.py

   # 自定义系统提示词版本
  python custom_chat_app.py

   # Gradio界面版本
   python gradio_chat_app.py

```

## 特色功能

1. **流式响应**
   - 实时显示AI响应
   - 打字机效果
   - 良好的用户体验

2. **系统提示词**
   - 可自定义AI角色
   - 实时更新
   - 保持会话一致性

3. **会话管理**
   - 自动保存历史
   - 可清除历史
   - 会话状态维护

## 扩展性

项目设计模块化，易于扩展：

- 可添加新的界面实现
- 可扩展消息处理功能
- 可添加新的API支持

## 贡献

欢迎提交 Pull Requests 来改进项目。对于重大更改，请先开 issue 讨论您想要更改的内容。

## 许可证

本项目采用 MIT 许可证。这意味着您可以：

- ✅ 自由使用
  - 可以在任何地方使用这份代码
  - 可以将其用于个人或商业项目

- ✅ 自由修改
  - 可以修改代码以适应您的需求
  - 可以基于此代码开发新功能

- ✅ 自由分发
  - 可以分享这份代码
  - 可以将其包含在您的项目中

- ✅ 自由商用
  - 可以将其用于商业项目
  - 可以基于此代码创建收费服务

唯一的要求是：

- 📝 保留版权声明和许可证声明
- 📝 对代码的任何实质性修改都应该注明

[完整的 MIT 许可证](LICENSE)

## 作者

[Namo1999](https://github.com/Namo1999)

## 致谢

- OpenAI API
- Gradio
- Flask
  