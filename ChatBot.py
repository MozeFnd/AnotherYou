# -*- coding: utf-8 -*-
from openai import OpenAI
from openai import AuthenticationError
from myToken import myToken

class ChatBot:
    """多轮对话机器人类，维护对话上下文"""
    
    def __init__(self, api_key, base_url="https://api-inference.modelscope.cn/v1/", 
                 model="Qwen/Qwen2.5-Coder-32B-Instruct", system_message="You are a helpful assistant."):
        """
        初始化聊天机器人
        
        Args:
            api_key: ModelScope Access Token
            base_url: API基础URL
            model: 模型名称
            system_message: 系统提示消息
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.messages = [
            {
                'role': 'system',
                'content': system_message
            }
        ]
    
    def chat(self, user_message, stream=True, print_response=True):
        """
        发送消息并获取AI回复
        
        Args:
            user_message: 用户消息
            stream: 是否使用流式输出
            print_response: 是否打印回复（流式输出时）
        
        Returns:
            str: AI的完整回复内容
        """
        if not user_message or not user_message.strip():
            return ""
        
        # 将用户消息添加到历史
        self.messages.append({
            'role': 'user',
            'content': user_message
        })
        
        try:
            # 发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=stream
            )
            
            # 收集AI的完整回答
            assistant_content = ""
            
            if stream:
                if print_response:
                    print("助手: ", end='', flush=True)
                
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        if print_response:
                            print(content, end='', flush=True)
                        assistant_content += content
                
                if print_response:
                    print()  # 换行
            else:
                assistant_content = response.choices[0].message.content
                if print_response:
                    print(f"助手: {assistant_content}")
            
            # 将AI回答添加到历史，用于下一轮对话
            if assistant_content:
                self.messages.append({
                    'role': 'assistant',
                    'content': assistant_content
                })
            
            return assistant_content
            
        except AuthenticationError as e:
            error_msg = f"认证错误: {e}\n请检查API key是否正确，是否已绑定阿里云账号"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"发生错误: {e}"
            print(error_msg)
            raise
    
    def clear_history(self, keep_system=True):
        """
        清除对话历史
        
        Args:
            keep_system: 是否保留系统消息
        """
        if keep_system and self.messages:
            system_msg = self.messages[0] if self.messages[0]['role'] == 'system' else None
            self.messages = [system_msg] if system_msg else []
        else:
            self.messages = []
    
    def get_history(self):
        """
        获取对话历史
        
        Returns:
            list: 对话历史消息列表
        """
        return self.messages.copy()
    
    def set_system_message(self, system_message):
        """
        设置系统消息
        
        Args:
            system_message: 新的系统消息
        """
        if self.messages and self.messages[0]['role'] == 'system':
            self.messages[0]['content'] = system_message
        else:
            self.messages.insert(0, {
                'role': 'system',
                'content': system_message
            })


# 使用示例
if __name__ == "__main__":
    # 创建聊天机器人实例
    bot = ChatBot(
        api_key=myToken,  # 请替换成您的ModelScope Access Token
        model="Qwen/Qwen2.5-Coder-32B-Instruct"
    )
    
    print("多轮对话已启动，输入 'exit' 或 'quit' 退出")
    print("-" * 50)
    
    try:
        while True:
            # 获取用户输入
            user_input = input("\n用户: ").strip()
            
            # 检查退出条件
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("对话结束，再见！")
                break
            
            if not user_input:
                print("请输入有效的问题")
                continue
            
            # 发送消息并获取回复
            bot.chat(user_input)
            
    except KeyboardInterrupt:
        print("\n\n对话已中断，再见！")
    except Exception as e:
        print(f"\n程序异常: {e}")
