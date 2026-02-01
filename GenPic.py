# -*- coding: utf-8 -*-
import requests
import time
import json
import os
import hashlib
from PIL import Image
from io import BytesIO
from myToken import myToken


class ImageGenerator:
    """图片生成器类，支持异步生成图片并保存到本地"""
    
    def __init__(self, api_key=None, base_url="https://api-inference.modelscope.cn/", 
                 model="Qwen/Qwen-Image", output_dir="images", poll_interval=3):
        """
        初始化图片生成器
        
        Args:
            api_key: ModelScope Access Token，如果为None则从myToken导入
            base_url: API基础URL
            model: 默认模型名称
            output_dir: 图片保存目录
            poll_interval: 轮询间隔（秒）
        """
        self.api_key = api_key if api_key else myToken
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.output_dir = output_dir
        self.poll_interval = poll_interval
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置通用请求头
        self.common_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _generate_md5(self, text):
        """生成文本的MD5哈希值"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def generate(self, prompt, model=None, **kwargs):
        """
        提交图片生成任务
        
        Args:
            prompt: 生成图片的提示词
            model: 模型名称，如果为None则使用默认模型
            **kwargs: 其他可选参数（如size, n, loras等）
        
        Returns:
            str: 任务ID (task_id)
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt不能为空")
        
        model = model or self.model
        request_data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/images/generations",
                headers={**self.common_headers, "X-ModelScope-Async-Mode": "true"},
                data=json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            )
            
            response.raise_for_status()
            task_id = response.json()["task_id"]
            return task_id
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"提交生成任务失败: {e}"
            if hasattr(e.response, 'text'):
                error_msg += f"\n错误详情: {e.response.text}"
            raise Exception(error_msg)
    
    def poll(self, task_id, prompt=None):
        """
        轮询任务状态，如果生成成功则保存图片并返回本地路径
        
        Args:
            task_id: 任务ID
            prompt: 提示词（用于生成文件名），如果为None则使用task_id
        
        Returns:
            str: 成功时返回图片的本地存储路径，失败时返回None
        """
        if prompt is None:
            prompt = task_id
        
        # 生成基于prompt的MD5文件名
        file_md5 = self._generate_md5(prompt)
        file_path = os.path.join(self.output_dir, f"{file_md5}.jpg")
        
        while True:
            try:
                result = requests.get(
                    f"{self.base_url}/v1/tasks/{task_id}",
                    headers={**self.common_headers, "X-ModelScope-Task-Type": "image_generation"},
                )
                result.raise_for_status()
                data = result.json()
                
                if data["task_status"] == "SUCCEED":
                    # 下载并保存图片
                    image_url = data["output_images"][0]
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    
                    # 保存图片
                    image = Image.open(BytesIO(image_response.content))
                    image.save(file_path)
                    
                    return file_path
                    
                elif data["task_status"] == "FAILED":
                    error_msg = data.get("error_message", "图片生成失败")
                    raise Exception(f"图片生成失败: {error_msg}")
                
                # 任务还在进行中，继续等待
                time.sleep(self.poll_interval)
                
            except requests.exceptions.HTTPError as e:
                raise Exception(f"轮询任务状态失败: {e}")
            except Exception as e:
                if "图片生成失败" in str(e):
                    raise
                raise Exception(f"轮询过程中发生错误: {e}")
    
    def generate_and_save(self, prompt, model=None, **kwargs):
        """
        生成图片并保存到本地（一步完成）
        
        Args:
            prompt: 生成图片的提示词
            model: 模型名称，如果为None则使用默认模型
            **kwargs: 其他可选参数
        
        Returns:
            str: 图片的本地存储路径
        """
        task_id = self.generate(prompt, model, **kwargs)
        return self.poll(task_id, prompt)


# 使用示例
if __name__ == "__main__":
    # 创建图片生成器实例
    generator = ImageGenerator(
        model="Qwen/Qwen-Image"  # 如果ZhipuAI模型不可用，使用Qwen模型
    )
    
    # 方式1: 分步执行（先提交任务，再轮询）
    prompt = "A golden cat"
    print(f"提交生成任务，提示词: {prompt}")
    task_id = generator.generate(prompt)
    print(f"任务ID: {task_id}")
    
    print("开始轮询任务状态...")
    image_path = generator.poll(task_id, prompt)
    print(f"图片已保存到: {image_path}")
    
    # 方式2: 一步完成（推荐）
    # prompt2 = "A beautiful sunset over the ocean"
    # image_path2 = generator.generate_and_save(prompt2)
    # print(f"图片已保存到: {image_path2}")