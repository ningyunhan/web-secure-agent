# llm-structured-output

让大模型稳定输出结构化 JSON 的 skill。

## 解决什么问题

LLM 输出的文本经常不规范：包一层 Markdown 代码块、多一句废话、缺字段、格式错误。下游代码一解析就报错。这个 skill 把"调用 LLM → 多层解析修正 → 返回可靠结构化对象"这个过程标准化了。

## 文件说明

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 方法论说明，给 AI agent 读取，告诉它遇到什么场景怎么处理 |
| `scripts/fixer.py` | JSON 修正管道，四层兜底（直接解析→去Markdown→提取大括号→Pydantic补全），可独立 import 使用 |
| `scripts/analyze.py` | 闭环执行脚本，接受参数直接运行，输出结构化 JSON 到 stdout |
| `references/examples.md` | 四个场景的完整使用示例（安全日志、客服工单、简历提取、资产指纹识别） |

## 两种用法

**直接运行拿结果：**

```bash
echo "192.168.1.1 POST /login password='or 1=1'" | \
  python scripts/analyze.py \
  --system-prompt "你是安全日志分析专家，提取告警类型和严重程度。只输出JSON。" \
  --schema '{"alert_type":"string","severity":"string","confidence":"number"}'
```

**集成到项目代码：**

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
    messages=[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
    temperature=0.1
)
alert = parse_and_fix(response.choices[0].message.content, Alert)
# alert 是合法的 Alert 对象，不会解析失败
```

## 依赖

- pydantic >= 2.0
- openai >= 1.0（仅 analyze.py 需要，fixer.py 不需要）
