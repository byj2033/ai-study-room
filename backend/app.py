from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder='../', static_url_path='')
CORS(app)  # 允许所有域名访问（仅测试用）

# 配置
DEEPSEEK_API_KEY = "YOUR_API_KEY_HERE"  # 稍后替换为你的真实API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 本地知识库（当API不可用时使用）
KNOWLEDGE_BASE = {
    "行测": {
        "modules": ["言语理解", "数量关系", "判断推理", "资料分析", "常识判断"],
        "time_management": "建议时间分配：常识5分钟，言语30分钟，数量15分钟，判断35分钟，资料25分钟，涂卡10分钟",
        "tips": "行测关键在于速度和准确率的平衡，先做擅长的模块"
    },
    "申论": {
        "structure": "大作文建议结构：总-分-总，五段三分式",
        "writing_tips": "1.紧扣材料 2.观点明确 3.论证充分 4.语言规范 5.卷面整洁"
    },
    "备考计划": {
        "30天": "基础(7天)→强化(14天)→冲刺(7天)→调整(2天)",
        "60天": "基础(15天)→专项(20天)→真题(15天)→模拟(10天)",
        "90天": "基础(20天)→提高(30天)→突破(25天)→保持(15天)"
    },
    "面试": {
        "types": ["结构化面试", "无领导小组讨论"],
        "preparation": "1.熟悉题型 2.模拟练习 3.积累素材 4.仪态训练 5.心理调适"
    }
}

@app.route('/')
def index():
    """主页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "AI公考自习室",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                "reply": "请输入您的问题。",
                "source": "local"
            })
        
        print(f"收到问题: {user_message}")
        
        # 1. 先检查本地知识库
        local_reply = check_local_knowledge(user_message)
        if local_reply:
            return jsonify({
                "reply": local_reply,
                "source": "local_knowledge"
            })
        
        # 2. 尝试调用DeepSeek API
        if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "YOUR_API_KEY_HERE":
            try:
                ai_reply = call_deepseek_api(user_message)
                if ai_reply:
                    return jsonify({
                        "reply": ai_reply,
                        "source": "deepseek_api"
                    })
            except Exception as api_error:
                print(f"API调用失败: {api_error}")
        
        # 3. 使用通用回复
        return jsonify({
            "reply": get_general_reply(user_message),
            "source": "general"
        })
        
    except Exception as e:
        print(f"处理聊天时出错: {e}")
        return jsonify({
            "reply": "抱歉，服务暂时遇到问题，请稍后再试。",
            "error": str(e),
            "source": "error"
        }), 500

def check_local_knowledge(question):
    """检查本地知识库"""
    question_lower = question.lower()
    
    # 关键词匹配
    keywords = {
        "行测": ["行测", "行政职业能力", "言语", "数量", "判断", "资料", "常识"],
        "申论": ["申论", "大作文", "小作文", "公文写作"],
        "计划": ["计划", "备考", "复习", "时间安排"],
        "面试": ["面试", "面谈", "结构化", "无领导"],
        "时政": ["时政", "时事", "热点", "新闻", "政策"]
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in question_lower:
                if category in KNOWLEDGE_BASE:
                    # 返回相关类别的知识
                    if category == "行测":
                        return f"关于行测：\n1. 包含模块：{', '.join(KNOWLEDGE_BASE['行测']['modules'])}\n2. 时间管理：{KNOWLEDGE_BASE['行测']['time_management']}\n3. 技巧：{KNOWLEDGE_BASE['行测']['tips']}"
                    elif category == "申论":
                        return f"关于申论：\n1. 结构建议：{KNOWLEDGE_BASE['申论']['structure']}\n2. 写作要点：{KNOWLEDGE_BASE['申论']['writing_tips']}"
                    elif category == "计划":
                        return f"备考计划建议：\n30天：{KNOWLEDGE_BASE['备考计划']['30天']}\n60天：{KNOWLEDGE_BASE['备考计划']['60天']}\n90天：{KNOWLEDGE_BASE['备考计划']['90天']}"
    
    return None

def call_deepseek_api(question):
    """调用DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建提示词
    system_prompt = """你是一位专业的公务员考试辅导老师，专门帮助考生备考。
你的回答应该：
1. 专业准确，基于公考实际
2. 实用具体，给出可操作建议
3. 鼓励积极，给予考生信心
4. 结构清晰，分点说明
5. 适当举例，帮助理解

当前考生的问题是关于公考的，请给出专业回答。"""
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"公考问题：{question}\n请给出专业、实用的回答。"}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    response = requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        json=payload,
        timeout=30  # 30秒超时
    )
    
    response.raise_for_status()
    result = response.json()
    
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    
    return None

def get_general_reply(question):
    """通用回复"""
    general_replies = [
        "这个问题很具体，建议你：1. 先系统学习相关知识点 2. 多做练习题 3. 总结错题规律",
        "备考中遇到这个问题很正常，关键是找到适合自己的学习方法，坚持练习会有进步的。",
        "关于这个问题，建议参考权威教材，同时结合历年真题进行针对性训练。",
        "可以尝试将这个大的问题分解成几个小问题，逐个击破，学习效果会更好。"
    ]
    
    import random
    return random.choice(general_replies)

@app.route('/api/create_plan', methods=['POST'])
def create_plan():
    """生成学习计划"""
    data = request.json
    days = data.get('days', 30)
    target = data.get('target', '全面提升')
    
    # 简单生成计划
    plan_template = f"""
📋 个性化{days}天备考计划（目标：{target}）

🎯 总体策略：
- 每天保持{min(6, max(4, days//10))}小时高效学习
- 每周休息1天调整状态
- 定期模拟测试检验效果

📅 阶段安排：

第一阶段：基础巩固（第1-{int(days*0.3)}天）
- 系统学习行测、申论基础知识
- 完成基础练习题
- 建立知识框架

第二阶段：专项突破（第{int(days*0.3)+1}-{int(days*0.7)}天）
- 针对薄弱环节重点训练
- 每周3套专项练习
- 整理错题本

第三阶段：冲刺模拟（第{int(days*0.7)+1}-{days}天）
- 严格按照考试时间模拟
- 复习高频考点
- 调整心态，查漏补缺

💡 每日安排建议：
上午（3小时）：行测模块练习
下午（3小时）：申论写作训练
晚上（1小时）：复习错题+时政学习

🔔 温馨提示：
1. 劳逸结合，保证充足睡眠
2. 定期总结，调整学习策略
3. 保持积极心态，相信自己
    """
    
    return jsonify({"plan": plan_template})

@app.route('/api/subjects')
def get_subjects():
    """获取学习科目列表"""
    return jsonify({
        "subjects": [
            {"id": 1, "name": "行测-言语理解", "questions": 150},
            {"id": 2, "name": "行测-数量关系", "questions": 120},
            {"id": 3, "name": "行测-判断推理", "questions": 180},
            {"id": 4, "name": "行测-资料分析", "questions": 100},
            {"id": 5, "name": "行测-常识判断", "questions": 200},
            {"id": 6, "name": "申论-概括归纳", "questions": 80},
            {"id": 7, "name": "申论-综合分析", "questions": 60},
            {"id": 8, "name": "申论-公文写作", "questions": 50},
            {"id": 9, "name": "申论-大作文", "questions": 40}
        ]
    })

if __name__ == '__main__':
    print("🚀 AI公考自习室后端启动中...")
    print(f"📁 静态文件目录: {app.static_folder}")
    print("🌐 请在浏览器访问: http://localhost:5000")
    print("🔄 按 Ctrl+C 停止服务")
    
    # 注意：debug=True仅用于开发
    app.run(debug=True, host='0.0.0.0', port=5000)