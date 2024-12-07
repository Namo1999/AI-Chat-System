from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from datetime import timedelta, datetime
import logging
from dataclasses import dataclass
from typing import List, Optional
import sys
import codecs

# 设置标准输出和错误输出的编码
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

@dataclass
class ChatMessage:
    role: str
    content: str

class ChatSession:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages: List[ChatMessage] = []
        self.initialize()
    
    def initialize(self):
        """初始化或重置会话"""
        self.messages = [ChatMessage(role='system', content=self.system_prompt)]
    
    def add_message(self, role: str, content: str):
        """添加新消息"""
        self.messages.append(ChatMessage(role=role, content=content))
    
    def get_messages(self) -> List[dict]:
        """获取用于API的消息格式"""
        return [{'role': msg.role, 'content': msg.content} for msg in self.messages]
    
    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            'messages': [{'role': msg.role, 'content': msg.content} 
                        for msg in self.messages]
        }
    
    @classmethod
    def from_messages(cls, messages: List[dict], system_prompt: str) -> 'ChatSession':
        """从消息列表创建会话，不添加系统提示词"""
        session = cls(system_prompt)
        session.messages = []  # 清空初始化时添加的系统提示词
        for msg in messages:
            session.add_message(msg['role'], msg['content'])
        return session

class ChatApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_app()
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        self.SYSTEM_PROMPT = """你是一个友善的AI助手，名叫小Q。你具有以下特点：
        1. 性格活泼开朗，说话幽默风趣
        2. 知识渊博，乐于解答各类问题
        3. 善于倾听，会给出贴心的建议
        4. 注重礼貌，谈吐得体
        请始终保持这个角色设定进行对话。
        """
    
    def setup_app(self):
        """设置Flask应用"""
        self.app.secret_key = "your-secret-key"
        self.app.permanent_session_lifetime = timedelta(days=1)
        self.app.config['SESSION_REFRESH_EACH_REQUEST'] = True
        
        # 注册路由
        self.app.route('/')(self.home)
        self.app.route('/chat', methods=['POST'])(self.chat)
        self.app.route('/clear', methods=['POST'])(self.clear_history)
        self.app.route('/get_history')(self.get_history)
        self.app.route('/debug_session')(self.debug_session)
    
    def get_chat_session(self) -> ChatSession:
        """获取或创建聊天会话"""
        chat_session = ChatSession(self.SYSTEM_PROMPT)
        
        if 'messages' in session:
            # 如果session中有消息，则加载它们
            for msg in session['messages']:
                if msg['role'] != 'system':  # 跳过系统消息，因为已经在初始化时添加
                    chat_session.add_message(msg['role'], msg['content'])
        
        return chat_session
    
    def save_chat_session(self, chat_session: ChatSession):
        """保存聊天会话到session"""
        session['messages'] = chat_session.to_dict()['messages']
        session.modified = True
    
    def home(self):
        """主页路由"""
        logger.info("访问主页")
        return render_template('index.html')
    
    def chat(self):
        """聊天接口"""
        try:
            user_message = request.json.get('message', '')
            if not user_message:
                logger.warning("收到空消息")
                return jsonify({'error': '消息不能为空'}), 400
                
            logger.info(f"收到用户消息: {user_message}")
            
            # 获取会话并添加用户消息
            chat_session = self.get_chat_session()
            logger.debug(f"当前会话消息数: {len(chat_session.messages)}")
            chat_session.add_message('user', user_message)
            self.save_chat_session(chat_session)
            
            # 调用API获取响应
            logger.debug("开始调用API")
            completion = self.client.chat.completions.create(
                model="qwen-plus",
                messages=chat_session.get_messages(),
                stream=False
            )
            
            # 获取AI响应
            ai_response = completion.choices[0].message.content
            logger.info(f"收到AI响应: {ai_response[:100]}...")  # 只记录前100个字符
            
            # 将AI响应添加到会话历史
            chat_session.add_message('assistant', ai_response)
            self.save_chat_session(chat_session)
            
            logger.info(f"会话已更新，当前消息数: {len(chat_session.messages)}")
            
            # 构造响应
            response_data = {
                'response': ai_response,
                'message_count': len(chat_session.messages)
            }
            logger.debug(f"返回数据: {response_data}")
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"生成响应时出错: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    def clear_history(self):
        """清除历史"""
        chat_session = ChatSession(self.SYSTEM_PROMPT)
        self.save_chat_session(chat_session)
        return jsonify({'status': 'success'})
    
    def get_history(self):
        """获取历史"""
        chat_session = self.get_chat_session()
        return jsonify({'messages': chat_session.get_messages()})
    
    def render_debug_html(self, debug_info: dict) -> str:
        """渲染调试页面的HTML"""
        html_content = f"""
        <html>
        <head>
            <title>Session Debug Info</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .message {{ 
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .system {{ background-color: #f0f0f0; }}
                .user {{ background-color: #e3f2fd; }}
                .assistant {{ background-color: #f1f8e9; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>Session Debug Information</h1>
            
            <div class="section">
                <h2>Session Info</h2>
                <pre>{json.dumps(debug_info['session_info'], indent=2)}</pre>
            </div>
            
            <div class="section">
                <h2>Messages</h2>
                {''.join(f'''
                <div class="message {msg['role'].lower()}">
                    <strong>#{msg['index']} - {msg['role']}</strong><br>
                    <pre>{msg['content']}</pre>
                </div>
                ''' for msg in debug_info['messages'])}
            </div>
        </body>
        </html>
        """
        return html_content
    
    def debug_session(self):
        """调试接口"""
        chat_session = self.get_chat_session()
        messages = chat_session.messages
        
        debug_info = {
            'session_info': {
                'session_id': id(session),
                'total_messages': len(messages),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'messages': [
                {
                    'index': i,
                    'role': msg.role.upper(),
                    'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content
                }
                for i, msg in enumerate(messages, 1)
            ]
        }
        
        if request.headers.get('accept', '').find('text/html') != -1:
            return self.render_debug_html(debug_info)
        return jsonify(debug_info)
    
    def run(self):
        """运行应用"""
        self.app.run(debug=True)

if __name__ == '__main__':
    chat_app = ChatApp()
    chat_app.run() 