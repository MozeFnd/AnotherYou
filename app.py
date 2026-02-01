# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory, Response
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS
import base64
import json
import os
import random
from ChatBot import ChatBot
from GenPic import ImageGenerator
from myToken import myToken

app = Flask(__name__, static_folder='static')
CORS(app)

# 1x1 PNG favicon to avoid 404s on /favicon.ico without adding a binary file.
_FAVICON_PNG = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="

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

@app.route('/favicon.ico')
def favicon():
    return Response(
        base64.b64decode(_FAVICON_PNG),
        mimetype='image/png'
    )

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
        
        formatted_answers = []
        for item in answers:
            if isinstance(item, dict):
                question = str(item.get('question', '')).strip()
                answer = str(item.get('answer', '')).strip()
                if question and answer:
                    formatted_answers.append(f"Q: {question}\nA: {answer}")
                elif answer:
                    formatted_answers.append(answer)
            elif item:
                formatted_answers.append(str(item))

        formatted_answers_text = "\n".join(formatted_answers)

        prompt = f"""根据以下信息生成一个详细的性格画像（控制在150字以内）：

基础信息：
- 性别：{gender}
- MBTI：{mbti}
- 星座：{zodiac}
- 家庭出身背景：{background}

性格测试答案：
{formatted_answers_text}

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

@app.route('/api/quiz_questions', methods=['POST'])
def quiz_questions():
    """随机生成性格测试问题"""
    try:
        data = request.json or {}
        basic_info = data.get('basic_info', {})
        seed = random.randint(1000, 9999)

        prompt = f"""你是性格测试设计师，请根据以下基础信息随机生成5个问题，每个问题提供3个简短选项，用于标定人物性格倾向。

基础信息：
- 性别：{basic_info.get('gender', '')}
- MBTI：{basic_info.get('mbti', '')}
- 星座：{basic_info.get('zodiac', '')}
- 家庭出身背景：{basic_info.get('background', '')}
- 随机种子：{seed}

要求：
1. 问题要具体、贴近日常场景
2. 选项要有区分度
3. 输出JSON，格式为：{{"questions":[{{"question":"...", "options":["...","...","..."]}}]}}
4. 只输出JSON，不要额外说明
"""

        chatbot.clear_history()
        raw = chatbot.chat(prompt, stream=False, print_response=False)

        def _parse_questions(text):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(text[start:end + 1])
                raise

        try:
            data_obj = _parse_questions(raw)
            questions = data_obj.get('questions', []) if isinstance(data_obj, dict) else []
            normalized = []
            for item in questions:
                question = str(item.get('question', '')).strip()
                options = item.get('options', [])
                options = [str(option).strip() for option in options if str(option).strip()]
                if question and options:
                    normalized.append({'question': question, 'options': options})
            if normalized:
                return jsonify({'success': True, 'questions': normalized})
        except Exception:
            pass

        fallback_pool = [
            {"question": "面对一项陌生任务，你更会先做什么？", "options": ["先拆解步骤再行动", "先行动再根据反馈调整", "先询问他人经验"]},
            {"question": "当你必须做决定时，你更看重？", "options": ["逻辑和数据", "直觉和感受", "过往经验"]},
            {"question": "在团队合作中你更像？", "options": ["组织者", "执行者", "协调者"]},
            {"question": "你如何应对压力？", "options": ["制定计划逐步解决", "用兴趣转移注意", "寻求支持与交流"]},
            {"question": "别人评价你时更常听到的是？", "options": ["理性", "温和", "果断"]},
            {"question": "当计划被打乱时，你会？", "options": ["迅速重新规划", "顺势而为", "先冷静观察"]},
            {"question": "你更喜欢哪种生活节奏？", "options": ["有序稳定", "灵活多变", "循序渐进"]},
            {"question": "遇到冲突时，你倾向于？", "options": ["直接沟通", "先冷静再处理", "尽量回避"]},
        ]
        random.shuffle(fallback_pool)
        return jsonify({'success': True, 'questions': fallback_pool[:5]})

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
3. 用中文描述，简洁明了
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
        
        # 生成图片（并行）
        prompt1 = f"comic style, {image_prompt1}, colorful, detailed"
        prompt2 = f"comic style, {image_prompt2}, colorful, detailed"
        print("正在并行生成前两张图片...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(
                image_generator.generate_and_save,
                prompt1,
                model="Qwen/Qwen-Image"
            )
            future2 = executor.submit(
                image_generator.generate_and_save,
                prompt2,
                model="Qwen/Qwen-Image"
            )
            image_path1 = future1.result()
            image_path2 = future2.result()
        
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

@app.route('/api/life_review', methods=['POST'])
def life_review():
    """生成整个人生回顾的简短描述"""
    try:
        data = request.json or {}
        user_data = data.get('user_data', {})
        stages = data.get('stages', [])
        basic_info = user_data.get('basic_info', {})
        personality = user_data.get('personality', '')

        stage_lines = []
        for item in stages:
            if not isinstance(item, dict):
                continue
            stage = item.get('stage', {})
            stage_name = stage.get('name', '某阶段')
            story = str(item.get('story', '')).strip()
            outcome = str(item.get('outcome', '')).strip()
            if story or outcome:
                stage_lines.append(f"{stage_name}：{story} 结局：{outcome}")

        stage_lines_text = "\n".join(stage_lines)

        prompt = f"""请根据以下信息生成一段100字以内的人生回顾总结，语言温暖、简洁，突出关键转折。

基础信息：
- 性别：{basic_info.get('gender', '')}
- MBTI：{basic_info.get('mbti', '')}
- 星座：{basic_info.get('zodiac', '')}
- 家庭出身背景：{basic_info.get('background', '')}
- 性格画像：{personality}

阶段内容：
{stage_lines_text}

请输出一段简短回顾："""

        chatbot.clear_history()
        summary = chatbot.chat(prompt, stream=False, print_response=False).strip()

        return jsonify({'success': True, 'summary': summary})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片文件服务"""
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860)
