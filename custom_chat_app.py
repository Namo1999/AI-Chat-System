from stream_chat_app import StreamChatApp, ChatSession
from flask import render_template, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

class CustomChatApp(StreamChatApp):
    def __init__(self):
        super().__init__()
        # 覆盖路由
        self.app.route('/')(self.home)
        self.app.route('/update_system_prompt', methods=['POST'])(self.update_system_prompt)
    
    def home(self):
        """主页路由"""
        logger.info("访问自定义聊天页面")
        return render_template('custom_chat.html', system_prompt=self.SYSTEM_PROMPT)
    
    def update_system_prompt(self):
        """更新系统提示词"""
        try:
            new_prompt = request.json.get('system_prompt', '')
            if not new_prompt:
                return jsonify({'error': '系统提示词不能为空'}), 400
            
            # 更新系统提示词
            self.SYSTEM_PROMPT = new_prompt
            
            # 清除现有会话
            session.pop('messages', None)
            
            # 创建新的会话
            chat_session = ChatSession(self.SYSTEM_PROMPT)
            self.save_messages_to_session(chat_session.get_messages())
            
            return jsonify({'status': 'success'})
            
        except Exception as e:
            logger.error(f"更新系统提示词时出错: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    chat_app = CustomChatApp()
    chat_app.run() 