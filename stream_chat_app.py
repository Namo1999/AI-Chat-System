from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from datetime import timedelta, datetime
import logging
from dataclasses import dataclass
from typing import List, Dict
import sys
import codecs
from threading import Lock

# 设置标准输出和错误输出的编码
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stream_chat.log', encoding='utf-8'),
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
        """初始化会话"""
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

class StreamChatApp:
    def __init__(self):
        self.app = Flask(__name__, template_folder='templates')
        self.setup_app()
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        # 用于临时存储完整响应的字典
        self.pending_responses: Dict[str, str] = {}
        self.response_lock = Lock()
        # 添加最大对话轮数制
        self.MAX_TURNS = 5
        
        self.SYSTEM_PROMPT = """你是一个友善的AI助手，名叫小Q。你具有以下特点：
        1. 性格活泼开朗，说话幽默风趣
        2. 知识渊博，乐于答各类问题
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
        self.app.route('/save_response', methods=['POST'])(self.save_response)
        self.app.route('/clear', methods=['POST'])(self.clear_history)
        self.app.route('/get_history')(self.get_history)
    
    def get_chat_session(self) -> ChatSession:
        """获取或创建聊天会话"""
        chat_session = ChatSession(self.SYSTEM_PROMPT)
        
        if 'messages' in session:
            logger.debug(f"从session加载消息: {session['messages']}")
            # 跳过第一条系统消息，直接加载后续消息
            for msg in session['messages'][1:]:
                chat_session.add_message(msg['role'], msg['content'])
        
        return chat_session
    
    def save_messages_to_session(self, messages: List[dict]):
        """保存消息列表到session"""
        session['messages'] = messages
        session.modified = True
    
    def save_response_to_session(self, response_id: str):
        """将完整响应保存到会话"""
        with self.response_lock:
            if response_id not in self.pending_responses:
                return
            
            complete_response = self.pending_responses[response_id]
            chat_session = self.get_chat_session()
            chat_session.add_message('assistant', complete_response)
            
            self.save_messages_to_session(chat_session.get_messages())
            
            # 清理临时存储
            del self.pending_responses[response_id]
            logger.debug(f"已保存响应到会话，当前消息数: {len(chat_session.messages)}")
    
    def home(self):
        """主页路由"""
        logger.info("访问主页")
        return render_template('stream_chat.html')
    
    def chat(self):
        """聊天接口 - 流式响应"""
        try:
            user_message = request.json.get('message', '')
            if not user_message:
                return jsonify({'error': '消息不能为空'}), 400
            
            logger.info(f"收到用户消息: {user_message}")
            
            # 获取会话并添加用户消息
            chat_session = self.get_chat_session()
            chat_session.add_message('user', user_message)
            self.save_messages_to_session(chat_session.get_messages())
            
            # 生成响应ID
            response_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            def generate():
                try:
                    messages = chat_session.get_messages()
                    logger.debug(f"发送到API的消息列表: {messages}")
                    
                    # 确保消息列表至少包含系统消息和用户消息
                    if len(messages) < 2:
                        logger.warning("消息列表过短，添加用户消息")
                        messages = [
                            {'role': 'system', 'content': self.SYSTEM_PROMPT},
                            {'role': 'user', 'content': user_message}
                        ]
                    
                    completion = self.client.chat.completions.create(
                        model="qwen-plus",
                        messages=messages,
                        stream=True
                    )
                    
                    collected_chunks = []
                    
                    for chunk in completion:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            collected_chunks.append(content)
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    
                    # 保存完整响应
                    complete_response = ''.join(collected_chunks)
                    logger.debug(f"收到完整响应: {complete_response}")
                    
                    # # 将完整响应添加到会话
                    # chat_session.add_message('assistant', complete_response)
                    # self.save_messages_to_session(chat_session.get_messages())
                    
                    # 保存到临时存储
                    with self.response_lock:
                        self.pending_responses[response_id] = complete_response
                    
                    # 发送完成标记和响应ID
                    yield f"data: {json.dumps({'status': 'complete', 'response_id': response_id})}\n\n"
                    
                except Exception as e:
                    logger.error(f"生成响应时出错: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
            
        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    def save_response(self):
        """保存响应到会话的端点"""
        response_id = request.json.get('response_id')
        if not response_id:
            return jsonify({'error': '缺少response_id'}), 400
        
        self.save_response_to_session(response_id)
        return jsonify({'status': 'success'})
    
    def clear_history(self):
        """清除历史"""
        # 清除 session 中的消息
        session.pop('messages', None)
        # 创建新的聊天会话（只包含系统提示）
        chat_session = ChatSession(self.SYSTEM_PROMPT)
        # 保存初始状态到 session
        self.save_messages_to_session(chat_session.get_messages())
        return jsonify({'status': 'success'})
    
    def get_history(self):
        """获取历史"""
        chat_session = self.get_chat_session()
        logger.info(chat_session.messages)    
        return jsonify({'messages': chat_session.get_messages()})
    
    def run(self):
        """运行应用"""
        self.app.run(debug=True, port=5001)  # 使用不同的端口

if __name__ == '__main__':
    chat_app = StreamChatApp()
    chat_app.run() 