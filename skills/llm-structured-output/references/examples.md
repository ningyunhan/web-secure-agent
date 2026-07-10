# 使用示例

## 场景一：安全日志分析

用户说："帮我分析这段日志，提取告警类型、严重程度、置信度"

agent 生成参数：
- system-prompt: "你是安全日志分析专家。分析日志文本提取告警信息。输出JSON，字段：alert_type（告警类型）, severity（严重程度）, confidence（置信度0-1）。只输出JSON，不要输出其他内容。"
- schema: {"alert_type":"string","severity":"string","confidence":"number"}
- input: "2024-01-15 10:32:45 192.168.1.100 POST /admin/login password='or 1=1' HTTP/1.1 200"

闭环执行：
```bash
echo "2024-01-15 10:32:45 192.168.1.100 POST /admin/login password='or 1=1' HTTP/1.1 200" | \
  python scripts/analyze.py \
  --system-prompt "你是安全日志分析专家。分析日志文本提取告警信息。输出JSON，字段：alert_type, severity, confidence。只输出JSON，不要输出其他内容。" \
  --schema '{"alert_type":"string","severity":"string","confidence":"number"}'
```

预期输出：
```json
{"alert_type": "sql_injection", "severity": "high", "confidence": 0.95}
```

集成代码：
```python
from openai import OpenAI
from pydantic import BaseModel
from fixer import parse_and_fix

class Alert(BaseModel):
    alert_type: str
    severity: str
    confidence: float

client = OpenAI(api_key="sk-xxx", base_url="https://api.deepseek.com/v1")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是安全日志分析专家。分析日志文本提取告警信息。输出JSON，字段：alert_type, severity, confidence。只输出JSON，不要输出其他内容。"},
        {"role": "user", "content": "2024-01-15 10:32:45 192.168.1.100 POST /admin/login password='or 1=1'"}
    ],
    temperature=0.1
)

alert = parse_and_fix(response.choices[0].message.content, Alert)
print(alert.alert_type)   # sql_injection
print(alert.severity)     # high
print(alert.confidence)   # 0.95
```

## 场景二：客服工单分类

用户说："帮我从这段客服投诉里提取工单类型、紧急程度、涉及产品"

agent 生成参数：
- system-prompt: "你是客服工单分析专家。分析工单文本提取结构化信息。输出JSON，字段：ticket_type（工单类型）, urgency（紧急程度）, product（涉及产品）。只输出JSON，不要输出其他内容。"
- schema: {"ticket_type":"string","urgency":"string","product":"string"}
- input: "客户反馈美团外卖订单超时未送达，骑手电话打不通，很着急"

闭环执行：
```bash
echo "客户反馈美团外卖订单超时未送达，骑手电话打不通，很着急" | \
  python scripts/analyze.py \
  --system-prompt "你是客服工单分析专家。分析工单文本提取结构化信息。输出JSON，字段：ticket_type, urgency, product。只输出JSON，不要输出其他内容。" \
  --schema '{"ticket_type":"string","urgency":"string","product":"string"}'
```

预期输出：
```json
{"ticket_type": "配送问题", "urgency": "高", "product": "美团外卖"}
```

## 场景三：简历信息提取

用户说："从这段自我介绍里提取姓名、技能列表、工作年限"

agent 生成参数：
- system-prompt: "你是简历分析专家。从自我介绍中提取结构化信息。输出JSON，字段：name（姓名）, skills（技能列表）, years（工作年限）。只输出JSON，不要输出其他内容。"
- schema: {"name":"string","skills":"string","years":"number"}
- input: "我叫张三，做了5年后端开发，主要用Python和Go，也写过一些前端Vue"

闭环执行：
```bash
echo "我叫张三，做了5年后端开发，主要用Python和Go，也写过一些前端Vue" | \
  python scripts/analyze.py \
  --system-prompt "你是简历分析专家。从自我介绍中提取结构化信息。输出JSON，字段：name, skills, years。只输出JSON，不要输出其他内容。" \
  --schema '{"name":"string","skills":"string","years":"number"}'
```

预期输出：
```json
{"name": "张三", "skills": "Python,Go,Vue", "years": 5.0}
```

## 场景四：资产指纹识别（本项目的原始场景）

用户说："识别这段Banner文本的服务名、版本、操作系统、端口、置信度"

agent 生成参数：
- system-prompt: "你是网络安全资产指纹识别专家。根据给定的网络Banner文本，识别出资产的标准化指纹信息。输出JSON，字段：service（服务名小写）, version（版本号或null）, os（操作系统或null）, port（端口号或null）, confidence（置信度0-1）。如果Banner被伪装或格式非标准，请尽力根据语义推断真实服务。只输出JSON，不要输出其他内容。"
- schema: {"service":"string","version":"string","os":"string","port":"string","confidence":"number"}
- input: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"

闭环执行：
```bash
echo "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1" | \
  python scripts/analyze.py \
  --system-prompt "你是网络安全资产指纹识别专家。根据Banner文本识别资产指纹。输出JSON，字段：service, version, os, port, confidence。只输出JSON，不要输出其他内容。" \
  --schema '{"service":"string","version":"string","os":"string","port":"string","confidence":"number"}'
```

预期输出：
```json
{"service": "openssh", "version": "8.9p1", "os": "Ubuntu", "port": "22", "confidence": 0.95}
```

## fixer.py 修正场景示例

LLM 返回了带 Markdown 包裹的输出：
```json
好的，分析结果如下：
```json
{"alert_type": "sql_injection", "severity": "high", "confidence": 0.95}
```
```

parse_and_fix 处理过程：
1. 直接 json.loads → 失败（有中文和代码块标记）
2. 去除 Markdown → 失败（前面还有"好的，分析结果如下："）
3. 提取大括号 → 成功提取 {"alert_type": "sql_injection", ...}
4. Pydantic 校验 → 通过，返回合法 Alert 对象

LLM 返回了缺字段的输出：
```json
{"alert_type": "sql_injection", "severity": "high"}
```

parse_and_fix 处理过程：
1. 直接 json.loads → 成功
2. Pydantic 校验 → 失败（缺 confidence）
3. 字段补全 → confidence 补默认值 0.5
4. 返回 Alert(alert_type="sql_injection", severity="high", confidence=0.5)
