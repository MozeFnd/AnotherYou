// 全局状态
let userData = null;
let currentStage = 0;
let currentStory = null;
let currentImages = [];

const STAGES = [
    { name: "幼儿时期", ageRange: "0-12岁" },
    { name: "少年时期", ageRange: "13-24岁" },
    { name: "青年时期", ageRange: "25-36岁" },
    { name: "中年时期", ageRange: "37-50岁" }
];

// 页面切换函数
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

// 获取图片URL
function getImageUrl(path) {
    if (!path) return '';
    const filename = path.split('/').pop();
    return `/images/${filename}`;
}

// 开始页面表单提交
document.getElementById('basic-info-form').addEventListener('submit', (e) => {
    e.preventDefault();
    showPage('quiz-page');
});

// 性格测试表单提交
document.getElementById('quiz-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const answers = [
        formData.get('q1'),
        formData.get('q2'),
        formData.get('q3'),
        formData.get('q4'),
        formData.get('q5')
    ];
    
    const basicInfo = {
        gender: document.getElementById('gender').value,
        mbti: document.getElementById('mbti').value,
        zodiac: document.getElementById('zodiac').value,
        background: document.getElementById('background').value
    };
    
    showPage('personality-page');
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                basic_info: basicInfo,
                answers: answers
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            userData = data.user_data;
            document.getElementById('personality-content').innerHTML = 
                `<p>${data.personality}</p>`;
            document.getElementById('start-journey-btn').style.display = 'block';
        } else {
            alert('生成性格画像失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error.message);
    }
});

// 开始人生之旅
document.getElementById('start-journey-btn').addEventListener('click', () => {
    currentStage = 0;
    loadStage();
});

// 加载阶段
async function loadStage() {
    if (currentStage >= STAGES.length) {
        alert('恭喜！你已经完成了所有人生阶段！');
        return;
    }
    
    showPage('game-page');
    updateProgress();
    
    const stage = STAGES[currentStage];
    document.getElementById('stage-title').textContent = stage.name;
    document.getElementById('stage-info').textContent = `年龄：${stage.ageRange}`;
    
    // 显示加载状态
    document.getElementById('story-content').innerHTML = 
        '<div class="loading">正在生成你的故事...</div>';
    document.getElementById('choice-section').style.display = 'none';
    document.getElementById('outcome-section').style.display = 'none';
    
    try {
        const response = await fetch('/api/generate_stage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stage_index: currentStage,
                user_data: userData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentStory = data.story;
            currentImages = data.images;
            
            // 显示故事和图片
            displayStory(data.story, data.images);
            
            // 显示选择题
            displayChoices(data.question, data.options);
        } else {
            alert('生成故事失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error.message);
    }
}

// 显示故事和图片
function displayStory(story, images) {
    let html = `<div class="story-text">${story}</div>`;
    
    images.forEach((image, index) => {
        html += `
            <div class="image-container">
                <img src="${getImageUrl(image.path)}" alt="故事图片 ${index + 1}">
                <div class="image-description">${image.description}</div>
            </div>
        `;
    });
    
    document.getElementById('story-content').innerHTML = html;
}

// 显示选择题
function displayChoices(question, options) {
    document.getElementById('choice-question').textContent = question;
    
    const optionsContainer = document.getElementById('choice-options');
    optionsContainer.innerHTML = '';
    
    options.forEach((option, index) => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'choice-option';
        optionDiv.textContent = option;
        optionDiv.addEventListener('click', () => {
            handleChoice(option);
        });
        optionsContainer.appendChild(optionDiv);
    });
    
    document.getElementById('choice-section').style.display = 'block';
}

// 处理用户选择
async function handleChoice(choice) {
    document.getElementById('choice-section').style.display = 'none';
    document.getElementById('outcome-section').style.display = 'block';
    document.getElementById('outcome-content').innerHTML = 
        '<div class="loading">正在生成结局...</div>';
    
    try {
        const response = await fetch('/api/generate_outcome', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stage_index: currentStage,
                user_data: userData,
                story: currentStory,
                choice: choice
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let html = `<div class="outcome-text">${data.outcome}</div>`;
            html += `
                <div class="image-container">
                    <img src="${getImageUrl(data.image.path)}" alt="结局图片">
                    <div class="image-description">${data.image.description}</div>
                </div>
            `;
            
            document.getElementById('outcome-content').innerHTML = html;
            
            // 显示下一阶段按钮
            if (currentStage < STAGES.length - 1) {
                document.getElementById('next-stage-btn').style.display = 'block';
            } else {
                document.getElementById('next-stage-btn').textContent = '完成人生之旅';
                document.getElementById('next-stage-btn').style.display = 'block';
            }
        } else {
            alert('生成结局失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error.message);
    }
}

// 下一阶段
document.getElementById('next-stage-btn').addEventListener('click', () => {
    if (currentStage < STAGES.length - 1) {
        currentStage++;
        loadStage();
    } else {
        alert('恭喜！你已经完成了所有人生阶段！');
    }
});

// 更新进度条
function updateProgress() {
    const progress = ((currentStage + 1) / STAGES.length) * 100;
    document.getElementById('progress').style.width = progress + '%';
}
