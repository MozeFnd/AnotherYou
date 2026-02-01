# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from ChatBot import ChatBot
from GenPic import ImageGenerator
from myToken import myToken

app = Flask(__name__, static_folder='static')
CORS(app)

# 初始化工具
chatbot = ChatBot(api_key=myToken)
image_generator = ImageGenerator()

# 游戏阶段定义
STAGES = [
    {"name": "幼儿时期", "age_range": "0-12岁"},
    {"name": "少年时期", "age_range": "13-24岁"},
    {"name": "青年时期", "age_range": "25-36岁"},
    {"name": "中年时期", "age_range": "37-50岁"}
]

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    """开始游戏，生成性格画像"""
    try:
        data = request.json
        basic_info = data.get('basic_info', {})
        answers = data.get('answers', [])
        
        # 构建性格画像生成提示
        gender = basic_info.get('gender', '')
        mbti = basic_info.get('mbti', '')
        zodiac = basic_info.get('zodiac', '')
        background = basic_info.get('background', '')
        
        prompt = f"""根据以下信息生成一个详细的性格画像（控制在150字以内）：

基础信息：
- 性别：{gender}
- MBTI：{mbti}
- 星座：{zodiac}
- 家庭出身背景：{background}

性格测试答案：{', '.join(answers)}

请生成一个生动、具体的性格画像，描述这个人的性格特点、行为倾向、价值观等。控制在150字以内。"""
        
        # 生成性格画像
        chatbot.clear_history()
        personality = chatbot.chat(prompt, stream=False, print_response=False)
        
        # 保存用户信息到session（简化版，实际应该用session或数据库）
        user_data = {
            'basic_info': basic_info,
            'personality': personality,
            'current_stage': 0,
            'stages_data': []
        }
        
        return jsonify({
            'success': True,
            'personality': personality,
            'user_data': user_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_stage', methods=['POST'])
def generate_stage():
    """生成某个阶段的故事和图片"""
    try:
        data = request.json
        stage_index = data.get('stage_index', 0)
        user_data = data.get('user_data', {})
        
        if stage_index >= len(STAGES):
            return jsonify({'success': False, 'error': '无效的阶段索引'}), 400
        
        stage = STAGES[stage_index]
        basic_info = user_data.get('basic_info', {})
        personality = user_data.get('personality', '')
        
        # 生成故事
        story_prompt = f"""你是一个人生故事模拟器。根据以下信息，生成一段{stage['name']}（{stage['age_range']}）正在发生的故事：

人物信息：
- 性别：{basic_info.get('gender', '')}
- MBTI：{basic_info.get('mbti', '')}
- 星座：{basic_info.get('zodiac', '')}
- 家庭背景：{basic_info.get('background', '')}
- 性格画像：{personality}

要求：
1. 故事要生动具体，符合该年龄段的特征
2. 故事要有冲突或选择点，但结局还未确定
3. 控制在200字以内
4. 故事要能引发读者的思考和选择

请生成故事："""
        
        chatbot.clear_history()
        story = chatbot.chat(story_prompt, stream=False, print_response=False)
        
        # 生成选择题
        choice_prompt = f"""基于以下故事，生成一个选择题，让用户决定故事的走向：

故事：{story}

要求：
1. 生成一个选择题，包含问题和2-3个选项
2. 选项要能影响故事的结局
3. 格式：问题\nA. 选项1\nB. 选项2\nC. 选项3（如果有）

请生成选择题："""
        
        choice_text = chatbot.chat(choice_prompt, stream=False, print_response=False)
        
        # 解析选择题
        lines = choice_text.strip().split('\n')
        question = lines[0] if lines else "你会如何选择？"
        options = [line.strip() for line in lines[1:] if line.strip() and (line.strip().startswith('A.') or line.strip().startswith('B.') or line.strip().startswith('C.'))]
        
        # 生成第一张图的prompt
        prompt1_text = f"""将以下故事转换为图片生成提示词（prompt）：

故事：{story}

要求：
1. 描述故事的开头场景
2. 适合漫画风格
3. 用英文描述，简洁明了
4. 包含场景、人物、情绪等细节

请生成prompt："""
        
        chatbot.clear_history()
        image_prompt1 = chatbot.chat(prompt1_text, stream=False, print_response=False)
        # 清理prompt，只保留英文描述
        image_prompt1 = image_prompt1.strip().replace('Prompt:', '').replace('prompt:', '').strip()
        if len(image_prompt1) > 500:
            image_prompt1 = image_prompt1[:500]
        
        # 生成第二张图的prompt
        prompt2_text = f"""将以下故事转换为图片生成提示词（prompt），描述故事发展到关键时刻的场景：

故事：{story}

要求：
1. 描述故事发展到关键时刻的场景
2. 适合漫画风格
3. 用英文描述，简洁明了
4. 包含场景、人物、情绪等细节

请生成prompt："""
        
        image_prompt2 = chatbot.chat(prompt2_text, stream=False, print_response=False)
        image_prompt2 = image_prompt2.strip().replace('Prompt:', '').replace('prompt:', '').strip()
        if len(image_prompt2) > 500:
            image_prompt2 = image_prompt2[:500]
        
        # 生成图片
        print(f"正在生成第一张图片...")
        image_path1 = image_generator.generate_and_save(
            f"comic style, {image_prompt1}, colorful, detailed",
            model="Qwen/Qwen-Image"
        )
        
        print(f"正在生成第二张图片...")
        image_path2 = image_generator.generate_and_save(
            f"comic style, {image_prompt2}, colorful, detailed",
            model="Qwen/Qwen-Image"
        )
        
        # 生成图片描述文字
        desc1_prompt = f"""为以下故事的开头场景生成一句简短的描述文字（20字以内）：

故事：{story}

请生成描述："""
        chatbot.clear_history()
        desc1 = chatbot.chat(desc1_prompt, stream=False, print_response=False).strip()
        
        desc2_prompt = f"""为以下故事的关键时刻场景生成一句简短的描述文字（20字以内）：

故事：{story}

请生成描述："""
        desc2 = chatbot.chat(desc2_prompt, stream=False, print_response=False).strip()
        
        return jsonify({
            'success': True,
            'story': story,
            'question': question,
            'options': options,
            'images': [
                {'path': image_path1, 'description': desc1},
                {'path': image_path2, 'description': desc2}
            ]
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_outcome', methods=['POST'])
def generate_outcome():
    """根据用户选择生成结局图片"""
    try:
        data = request.json
        stage_index = data.get('stage_index', 0)
        user_data = data.get('user_data', {})
        story = data.get('story', '')
        choice = data.get('choice', '')
        
        if stage_index >= len(STAGES):
            return jsonify({'success': False, 'error': '无效的阶段索引'}), 400
        
        stage = STAGES[stage_index]
        
        # 生成结局故事
        outcome_prompt = f"""基于以下故事和用户的选择，生成故事的结局：

原故事：{story}
用户选择：{choice}
阶段：{stage['name']}（{stage['age_range']}）

要求：
1. 根据用户的选择，生成一个合理的结局
2. 结局要符合人物的性格和背景
3. 控制在150字以内
4. 结局要有意义，能体现选择的影响

请生成结局："""
        
        chatbot.clear_history()
        outcome = chatbot.chat(outcome_prompt, stream=False, print_response=False)
        
        # 生成结局图片的prompt
        image_prompt_text = f"""将以下结局转换为图片生成提示词（prompt）：

结局：{outcome}

要求：
1. 描述结局的场景
2. 适合漫画风格
3. 用英文描述，简洁明了
4. 包含场景、人物、情绪等细节

请生成prompt："""
        
        image_prompt = chatbot.chat(image_prompt_text, stream=False, print_response=False)
        image_prompt = image_prompt.strip().replace('Prompt:', '').replace('prompt:', '').strip()
        if len(image_prompt) > 500:
            image_prompt = image_prompt[:500]
        
        # 生成结局图片
        print(f"正在生成结局图片...")
        image_path = image_generator.generate_and_save(
            f"comic style, {image_prompt}, colorful, detailed",
            model="Qwen/Qwen-Image"
        )
        
        # 生成结局描述
        desc_prompt = f"""为以下结局生成一句简短的描述文字（20字以内）：

结局：{outcome}

请生成描述："""
        chatbot.clear_history()
        desc = chatbot.chat(desc_prompt, stream=False, print_response=False).strip()
        
        return jsonify({
            'success': True,
            'outcome': outcome,
            'image': {'path': image_path, 'description': desc}
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片文件服务"""
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
