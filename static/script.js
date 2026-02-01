// 全局状态
let userData = null;
let currentStage = 0;
let currentStory = null;
let currentImages = [];
let stageHistory = [];
let quizQuestions = [];
let reviewSummaryText = '';

const API_BASE = window.API_BASE || (() => {
    const { protocol, hostname, port } = window.location;
    if ((hostname === 'localhost' || hostname === '127.0.0.1') && port && port !== '7860') {
        return `${protocol}//${hostname}:7860`;
    }
    return '';
})();

async function parseJsonResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return response.json();
    }
    const text = await response.text();
    throw new Error(`服务返回非JSON：${text.slice(0, 200)}`);
}

function apiFetch(path, options) {
    return fetch(`${API_BASE}${path}`, options);
}

const STAGES = [
    { name: "幼儿时期", ageRange: "0-12岁" },
    { name: "少年时期", ageRange: "13-24岁" },
    { name: "青年时期", ageRange: "25-36岁" },
    { name: "中年时期", ageRange: "37-50岁" }
];

function getFactsForStage(stageIndex) {
    if (!window.FACTS || !Array.isArray(window.FACTS.stages)) {
        return [];
    }

    const directStage = window.FACTS.stages[stageIndex];
    if (directStage && Array.isArray(directStage.facts)) {
        return directStage.facts;
    }

    const stageMeta = STAGES[stageIndex];
    if (stageMeta) {
        const matched = window.FACTS.stages.find((stage) => {
            return stage.name === stageMeta.name || stage.ageRange === stageMeta.ageRange;
        });
        if (matched && Array.isArray(matched.facts)) {
            return matched.facts;
        }
    }

    return [];
}

function pickRandomItems(items, count) {
    const copy = items.slice();
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy.slice(0, count);
}

function sanitizeFactText(text) {
    if (!text) {
        return '';
    }
    let cleaned = String(text);
    cleaned = cleaned.replace(/公元前\s*\d+\s*年/g, '');
    cleaned = cleaned.replace(/\d{3,4}\s*年/g, '');
    cleaned = cleaned.replace(/\d+\s*岁/g, '');
    cleaned = cleaned.replace(/^[，,。\s]*时/, '');
    cleaned = cleaned.replace(/^[，,。\s]*/, '');
    return cleaned;
}

function renderFacts(stageIndex, count = 3) {
    const facts = getFactsForStage(stageIndex);
    if (!facts.length) {
        return '';
    }

    const selected = pickRandomItems(facts, Math.min(count, facts.length));
    const listItems = selected.map((fact) => {
        const stageLabel = STAGES[stageIndex] ? STAGES[stageIndex].name : '';
        const metaParts = [fact.person, stageLabel].filter(Boolean);
        const metaText = metaParts.join(' · ');
        const cleanedText = sanitizeFactText(fact.text || '');
        const stageHints = ['童年时期', '少年时期', '青年时期', '中年时期', '幼年', '童年', '青年', '中年'];
        const hasStageHint = stageLabel ? [stageLabel, ...stageHints].some((hint) => cleanedText.includes(hint)) : false;
        const prefix = stageLabel && !hasStageHint ? `在${stageLabel}` : '';
        const sentence = `你知道吗？${fact.person || ''}${prefix}${cleanedText}`;
        const sourceText = fact.source ? `<span class="fact-source">来源：${fact.source}</span>` : '';
        return `
            <li class="fact-item">
                <div class="fact-meta">${metaText}</div>
                <div class="fact-text">${sentence}</div>
                ${sourceText}
            </li>
        `;
    }).join('');

    return `
        <div class="facts-panel">
            <div class="facts-header">名人轶事</div>
            <ul class="facts-list">
                ${listItems}
            </ul>
        </div>
    `;
}

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

function getBasicInfo() {
    return {
        gender: document.getElementById('gender').value,
        mbti: document.getElementById('mbti').value,
        zodiac: document.getElementById('zodiac').value,
        background: document.getElementById('background').value
    };
}

function renderQuizQuestions(questions) {
    const container = document.getElementById('quiz-items');
    if (!questions || !questions.length) {
        container.innerHTML = '<div class="loading">暂无可用问题，请稍后再试。</div>';
        return;
    }

    container.innerHTML = '';
    questions.forEach((item, index) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'quiz-item';

        const title = document.createElement('h3');
        title.textContent = `问题 ${index + 1}：${item.question}`;
        wrapper.appendChild(title);

        const options = Array.isArray(item.options) ? item.options : [];
        options.forEach((option, optionIndex) => {
            const label = document.createElement('label');
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = `q${index}`;
            input.value = option;
            label.appendChild(input);
            label.appendChild(document.createTextNode(` ${option}`));
            wrapper.appendChild(label);
        });

        const customWrapper = document.createElement('div');
        customWrapper.className = 'quiz-custom';
        const customInput = document.createElement('input');
        customInput.type = 'text';
        customInput.placeholder = '或填写你的回答';
        customInput.className = 'quiz-custom-input';
        customInput.dataset.questionIndex = index;
        customWrapper.appendChild(customInput);
        wrapper.appendChild(customWrapper);

        container.appendChild(wrapper);
    });
}

async function loadQuizQuestions(basicInfo) {
    const container = document.getElementById('quiz-items');
    container.innerHTML = '<div class="loading">正在生成性格问题...</div>';
    quizQuestions = [];

    try {
        const response = await apiFetch('/api/quiz_questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ basic_info: basicInfo })
        });
        const data = await parseJsonResponse(response);
        if (data.success) {
            quizQuestions = data.questions || [];
            renderQuizQuestions(quizQuestions);
        } else {
            container.innerHTML = `<div class="loading">生成问题失败：${data.error}</div>`;
        }
    } catch (error) {
        container.innerHTML = `<div class="loading">请求失败：${error.message}</div>`;
    }
}

// 开始页面表单提交
document.getElementById('basic-info-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const basicInfo = getBasicInfo();
    showPage('quiz-page');
    loadQuizQuestions(basicInfo);
});

// 性格测试表单提交
document.getElementById('quiz-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!quizQuestions.length) {
        alert('题目尚未生成，请稍后再试。');
        return;
    }

    const answers = [];
    for (let i = 0; i < quizQuestions.length; i++) {
        const customInput = document.querySelector(`.quiz-custom-input[data-question-index="${i}"]`);
        const customValue = customInput ? customInput.value.trim() : '';
        const selected = document.querySelector(`input[name="q${i}"]:checked`);
        const answer = customValue || (selected ? selected.value : '');
        if (!answer) {
            alert(`请完成第 ${i + 1} 题`);
            return;
        }
        answers.push({
            question: quizQuestions[i].question,
            answer: answer
        });
    }
    
    const basicInfo = getBasicInfo();
    
    showPage('personality-page');
    
    try {
        const response = await apiFetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                basic_info: basicInfo,
                answers: answers
            })
        });
        const data = await parseJsonResponse(response);
        
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
    stageHistory = [];
    reviewSummaryText = '';
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
        `<div class="loading">正在生成你的故事...</div>${renderFacts(currentStage)}`;
    document.getElementById('choice-section').style.display = 'none';
    document.getElementById('outcome-section').style.display = 'none';
    
    try {
        const response = await apiFetch('/api/generate_stage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stage_index: currentStage,
                user_data: userData
            })
        });
        const data = await parseJsonResponse(response);
        
        if (data.success) {
            currentStory = data.story;
            currentImages = data.images;
            stageHistory[currentStage] = {
                stage: stage,
                story: data.story,
                images: data.images
            };
            
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
        `<div class="loading">正在生成结局...</div>${renderFacts(currentStage)}`;
    
    try {
        const response = await apiFetch('/api/generate_outcome', {
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
        const data = await parseJsonResponse(response);
        
        if (data.success) {
            let html = `<div class="outcome-text">${data.outcome}</div>`;
            html += `
                <div class="image-container">
                    <img src="${getImageUrl(data.image.path)}" alt="结局图片">
                    <div class="image-description">${data.image.description}</div>
                </div>
            `;
            
            document.getElementById('outcome-content').innerHTML = html;
            if (!stageHistory[currentStage]) {
                stageHistory[currentStage] = { stage: STAGES[currentStage] };
            }
            stageHistory[currentStage].outcome = data.outcome;
            stageHistory[currentStage].outcomeImage = data.image;
            
            // 显示下一阶段按钮
            if (currentStage < STAGES.length - 1) {
                document.getElementById('next-stage-btn').style.display = 'block';
            } else {
                document.getElementById('next-stage-btn').textContent = '人生回顾';
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
        showReview();
    }
});

function renderReviewComic() {
    const container = document.getElementById('review-comic');
    container.innerHTML = '';

    const frames = [];
    stageHistory.forEach((item, index) => {
        if (!item) {
            return;
        }
        const stageLabel = item.stage ? item.stage.name : `阶段 ${index + 1}`;
        (item.images || []).forEach((image) => {
            frames.push({
                stageLabel,
                image: image
            });
        });
        if (item.outcomeImage) {
            frames.push({
                stageLabel,
                image: item.outcomeImage
            });
        }
    });

    if (!frames.length) {
        container.innerHTML = '<div class="loading">暂无连环画内容。</div>';
        return;
    }

    frames.forEach((frame, index) => {
        const frameDiv = document.createElement('div');
        frameDiv.className = 'review-frame';
        frameDiv.style.setProperty('--delay', `${index * 0.08}s`);

        const img = document.createElement('img');
        img.src = getImageUrl(frame.image.path);
        img.alt = `回顾图片 ${index + 1}`;

        const caption = document.createElement('div');
        caption.className = 'review-caption';
        caption.textContent = frame.stageLabel;

        frameDiv.appendChild(img);
        frameDiv.appendChild(caption);
        container.appendChild(frameDiv);
    });
}

async function showReview() {
    showPage('review-page');
    renderReviewComic();
    const summaryBox = document.getElementById('review-summary');
    summaryBox.innerHTML = '<div class="loading">正在生成回顾...</div>';
    reviewSummaryText = '';

    try {
        const response = await apiFetch('/api/life_review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_data: userData,
                stages: stageHistory
            })
        });
        const data = await parseJsonResponse(response);
        if (data.success) {
            reviewSummaryText = data.summary || '';
            summaryBox.innerHTML = `<p>${reviewSummaryText}</p>`;
        } else {
            summaryBox.innerHTML = `<div class="loading">生成回顾失败：${data.error}</div>`;
        }
    } catch (error) {
        summaryBox.innerHTML = `<div class="loading">请求失败：${error.message}</div>`;
    }
}

document.getElementById('review-animate-toggle').addEventListener('change', (e) => {
    const comic = document.getElementById('review-comic');
    if (e.target.checked) {
        comic.classList.add('animate');
    } else {
        comic.classList.remove('animate');
    }
});

document.getElementById('review-audio-btn').addEventListener('click', () => {
    if (!reviewSummaryText) {
        return;
    }
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(reviewSummaryText);
        utterance.lang = 'zh-CN';
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }
});

document.getElementById('restart-btn').addEventListener('click', () => {
    showPage('start-page');
});

// 更新进度条
function updateProgress() {
    const progress = ((currentStage + 1) / STAGES.length) * 100;
    document.getElementById('progress').style.width = progress + '%';
}
