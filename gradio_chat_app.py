import gradio as gr
from stream_chat_app import StreamChatApp, ChatSession
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class GradioChatApp(StreamChatApp):
    def __init__(self):
        super().__init__()
        self.chat_history: List[Tuple[str, str]] = []
        self.current_session = ChatSession(self.SYSTEM_PROMPT)
    
    def chat_response(
        self, 
        message: str, 
        history: List[Tuple[str, str]], 
        system_prompt: str
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """处理聊天消息并返回响应"""
        try:
            # 如果系统提示词改变，更新它
            if system_prompt != self.SYSTEM_PROMPT:
                self.SYSTEM_PROMPT = system_prompt
                self.current_session = ChatSession(self.SYSTEM_PROMPT)
                # 重新添加历史消息
                for user_msg, bot_msg in history:
                    self.current_session.add_message('user', user_msg)
                    self.current_session.add_message('assistant', bot_msg)
            
            # 添加用户消息
            self.current_session.add_message('user', message)
            
            # 获取AI响应
            messages = self.current_session.get_messages()
            completion = self.client.chat.completions.create(
                model="qwen-plus",
                messages=messages,
                stream=False  # Gradio不需要流式响应
            )
            
            response = completion.choices[0].message.content
            
            # 添加助手消息
            self.current_session.add_message('assistant', response)
            
            # 更新历史
            new_history = history + [(message, response)]
            
            # 返回空字符串作为第一个返回值，这样会清空输入框
            return "", new_history
            
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
            return "", history  # 发生错误时也返回空字符串
    
    def clear_history(self) -> Tuple[str, List[Tuple[str, str]], str]:
        """清除聊天历史"""
        self.current_session = ChatSession(self.SYSTEM_PROMPT)
        return "", [], self.SYSTEM_PROMPT
    
    def create_ui(self):
        """创建Gradio界面"""
        with gr.Blocks() as demo:
            with gr.Row():
                with gr.Column():
                    system_prompt = gr.Textbox(
                        value=self.SYSTEM_PROMPT,
                        label="系统提示词",
                        lines=5,
                        placeholder="输入AI助手的人设..."
                    )
                    
                    chatbot = gr.Chatbot(
                        label="聊天历史",
                        height=400
                    )
                    
                    msg = gr.Textbox(
                        label="输入消息",
                        placeholder="请输入您的消息...",
                        lines=2
                    )
                    
                    with gr.Row():
                        submit = gr.Button("发送")
                        clear = gr.Button("清除历史")
            
            # 处理发送消息
            submit_click = submit.click(
                fn=self.chat_response,
                inputs=[msg, chatbot, system_prompt],
                outputs=[msg, chatbot]
            )
            
            # 处理按回车发送
            msg.submit(
                fn=self.chat_response,
                inputs=[msg, chatbot, system_prompt],
                outputs=[msg, chatbot]
            )
            
            # 处理清除历史
            clear.click(
                fn=self.clear_history,
                inputs=[],
                outputs=[msg, chatbot, system_prompt]
            )
            
        return demo

def main():
    app = GradioChatApp()
    demo = app.create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True
    )

if __name__ == "__main__":
    main() 