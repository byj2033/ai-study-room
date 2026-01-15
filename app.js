// 配置信息 - 后面部署时会修改
const CONFIG = {
    apiUrl: 'http://localhost:5000/api',  // 本地测试用
    status: 'development'
};

// DOM元素
let chatArea, userInput, statusText, typingIndicator;

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    chatArea = document.getElementById('chatArea');
    userInput = document.getElementById('userInput');
    statusText = document.getElementById('statusText');
    typingIndicator = document.getElementById('typingIndicator');
    
    // 初始状态
    updateStatus('connected', '✅ AI服务已连接，可以开始提问');
    
    // 让输入框自动获取焦点
    userInput.focus();
});

// 更新状态显示
function updateStatus(type, message) {
    const statusEl = statusText;
    const parent = statusEl.parentElement;
    
    switch(type) {
        case 'connected':
            parent.className = 'alert alert-success d-flex align-items-center';
            break;
        case 'error':
            parent.className = 'alert alert-danger d-flex align-items-center';
            break;
        case 'connecting':
            parent.className = 'alert alert-warning d-flex align-items-center';
            break;
    }
    statusEl.innerHTML = message;
}

// 发送消息
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // 显示用户消息
    addMessage(message, 'user');
    userInput.value = '';
    
    // 显示"正在输入"指示器
    showTyping(true);
    
    try {
        // 发送到后端API
        const response = await fetch(`${CONFIG.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                timestamp: new Date().toISOString()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 隐藏"正在输入"指示器
        showTyping(false);
        
        // 显示AI回复
        if (data.reply) {
            addMessage(data.reply, 'ai');
        } else {
            addMessage('抱歉，我没有理解您的问题，请换种方式提问。', 'ai');
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        showTyping(false);
        
        // 离线模式：使用预定义回答
        const fallbackReply = getFallbackReply(message);
        addMessage(fallbackReply, 'ai');
        
        updateStatus('error', '⚠️ 网络不稳定，使用离线回答模式');
    }
}

// 快捷提问
function quickQuestion(question) {
    userInput.value = question;
    sendMessage();
}

// 添加消息到聊天区域
function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'user-msg' : 'ai-msg';
    
    // 格式化文本，保留换行
    const formattedText = text.replace(/\n/g, '<br>');
    msgDiv.innerHTML = formattedText;
    
    chatArea.appendChild(msgDiv);
    
    // 滚动到底部
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 显示/隐藏"正在输入"指示器
function showTyping(show) {
    typingIndicator.style.display = show ? 'block' : 'none';
    
    if (show) {
        // 滚动到底部显示正在输入
        chatArea.scrollTop = chatArea.scrollHeight;
    }
}

// 离线模式备用回答
function getFallbackReply(question) {
    const fallbackAnswers = {
        '行测': '行测包括言语理解、数量关系、判断推理、资料分析和常识判断五大模块。建议先从自己擅长的模块开始，每天保持练习。',
        '申论': '申论考察阅读理解、综合分析、提出对策和文字表达能力。重点是多读材料、多写多练，积累规范用语。',
        '时政': '建议关注人民日报、新华社、学习强国等官方平台，重点关注近一年的重要会议、政策文件和热点事件。',
        '计划': '制定备考计划要考虑：1.明确考试时间 2.评估自身基础 3.合理分配各模块时间 4.定期模拟测试 5.留出复习时间',
        '面试': '公务员面试注重：1.仪表仪态 2.语言表达 3.逻辑思维 4.政策理解 5.应急处理能力。建议多进行模拟练习。'
    };
    
    // 查找关键词
    for (const [key, answer] of Object.entries(fallbackAnswers)) {
        if (question.includes(key)) {
            return answer;
        }
    }
    
    return '这个问题需要联网获取最新信息。目前我只能提供基础建议：保持每天4-6小时高效学习，定期模拟测试，及时复习错题。';
}

// 生成学习计划
function generatePlan() {
    const days = prompt('请输入备考天数（如30、60、90）：', '30');
    if (!days) return;
    
    const plan = `📅 为你生成的${days}天备考计划：
    
第一阶段（第1-${Math.floor(days*0.3)}天）：基础学习
- 行测各模块基础知识系统学习
- 申论基本题型和方法掌握
- 每天做一套模块练习题

第二阶段（第${Math.floor(days*0.3)+1}-${Math.floor(days*0.7)}天）：强化训练
- 专项突破薄弱环节
- 每周2-3套完整真题
- 整理错题本，定期复习

第三阶段（第${Math.floor(days*0.7)+1}-${days}天）：冲刺模拟
- 严格按照考试时间模拟
- 重点复习高频考点
- 调整心态，保持状态

💡 建议：每天保持4-6小时高效学习，周末进行模拟考试。`;
    
    addMessage(plan, 'ai');
}

// 开始专注计时器
function startTimer() {
    const minutes = 25;
    let timeLeft = minutes * 60;
    
    addMessage(`⏱️ 开始${minutes}分钟专注学习！请专心复习，计时结束后我会提醒你。`, 'ai');
    
    const timerMsg = addMessage(`剩余时间：${minutes}:00`, 'ai');
    timerMsg.id = 'timerMessage';
    
    const timerInterval = setInterval(() => {
        timeLeft--;
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        
        document.getElementById('timerMessage').innerHTML = 
            `剩余时间：${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            addMessage('⏰ 时间到！休息5分钟再继续学习吧！', 'ai');
            document.getElementById('timerMessage').innerHTML = '计时结束！';
        }
    }, 1000);
}

// 显示帮助
function showHelp() {
    const helpText = `🤔 使用帮助：
    
1. 直接输入问题，按Enter或点击发送
2. 点击快捷按钮快速提问
3. 点击"生成个性化计划"制定备考计划
4. 点击"开始25分钟专注"进入番茄钟学习
    
📱 功能说明：
- 智能答疑：解答公考相关问题
- 离线备用：网络不佳时使用本地知识库
- 学习计时：帮助保持专注
    
⚠️ 注意：这是测试版本，功能会持续更新！`;
    
    alert(helpText);
}

// 添加快捷键支持
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        // Ctrl+Enter 清空输入
        userInput.value = '';
    } else if (e.key === 'Escape') {
        // ESC 清除焦点
        userInput.blur();
    }
});

// 导出函数供HTML调用（如果需要）
window.sendMessage = sendMessage;
window.quickQuestion = quickQuestion;
window.generatePlan = generatePlan;
window.startTimer = startTimer;
window.showHelp = showHelp;