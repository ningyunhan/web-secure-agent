# 使用示例

## 场景一：运维 FAQ 语义检索

用户说："我有一批公司内部的运维 FAQ，想做一个语义检索功能"

### 闭环执行

```bash
# 初始化知识库
python scripts/kb.py init --path ./data/ops_faq

# 添加 FAQ
python scripts/kb.py add \
  --path ./data/ops_faq \
  --type faq \
  --title "MySQL连接超时排查" \
  --content "检查max_connections参数是否过小，检查网络连通性，检查连接池配置" \
  --tags "mysql,超时,连接"

python scripts/kb.py add \
  --path ./data/ops_faq \
  --type faq \
  --title "Redis内存溢出处理" \
  --content "检查maxmemory配置，使用SCAN查看大key，设置淘汰策略" \
  --tags "redis,内存,OOM"

# 语义检索
python scripts/kb.py search \
  --path ./data/ops_faq \
  --query "数据库连不上" \
  --top-k 3
```

预期输出：
```json
[
  {
    "title": "MySQL连接超时排查",
    "content": "检查max_connections参数是否过小...",
    "similarity": 78,
    "distance": 0.33
  }
]
```

### 集成代码

```python
from kb import VectorKB

kb = VectorKB("./data/ops_faq")

# 批量导入
for faq in faq_list:
    kb.add(type="faq", title=faq["question"], content=faq["answer"], tags=faq["category"])

# 检索
results = kb.search("数据库连接超时", top_k=3)
for r in results:
    print(f"[{r['similarity']}分] {r['title']}")
    print(r["content"])

# 添加新 FAQ（立即生效）
kb.add(type="faq", title="Redis连接超时排查", content="检查timeout参数...")

# 禁用旧 FAQ（软删除）
kb.update_status(id="abc-123", status="inactive")

# 编辑
kb.update(id="abc-456", type="faq", title="MySQL连接超时(更新)", content="新内容")

# 删除
kb.delete(id="abc-789")
```

## 场景二：安全规则知识库

用户说："我有一批安全检测规则，想根据输入的告警信息检索相关的处理 SOP"

```bash
# 初始化
python scripts/kb.py init --path ./data/security_rules

# 添加规则
python scripts/kb.py add \
  --path ./data/security_rules \
  --type rule \
  --title "SQL注入检测规则" \
  --content "当请求参数中出现union select、or 1=1、sleep()等SQL注入特征时触发告警" \
  --tags "sqli,web,注入"

python scripts/kb.py add \
  --path ./data/security_rules \
  --type sop \
  --title "SQL注入应急SOP" \
  --content "1.确认攻击来源IP 2.封禁IP 3.检查WAF规则 4.排查数据泄露" \
  --tags "sqli,应急"

# 检索
python scripts/kb.py search \
  --path ./data/security_rules \
  --query "select * from users where 1=1" \
  --top-k 3
```

## 场景三：企业内部文档检索

用户说："我们有几百篇内部技术文档，想做个智能搜索"

```bash
# 批量添加（agent 可以遍历文档目录自动生成 add 命令）
python scripts/kb.py add \
  --path ./data/docs_kb \
  --type article \
  --title "微服务架构设计指南" \
  --content "本文档介绍微服务拆分原则、服务间通信方案..." \
  --tags "架构,微服务"

# 检索
python scripts/kb.py search \
  --path ./data/docs_kb \
  --query "服务之间怎么通信" \
  --top-k 5
```

## 场景四：和第一个 skill 组合使用

用户说："帮我分析这段日志提取告警信息，然后检索相关的处理 SOP"

agent 先用第一个 skill（llm-structured-output）提取结构化告警：

```bash
echo "192.168.1.1 POST /login password='or 1=1'" | \
  python ../llm-structured-output/scripts/analyze.py \
  --system-prompt "你是安全日志分析专家，提取告警类型和严重程度。输出JSON。" \
  --schema '{"alert_type":"string","severity":"string"}'
```

拿到结果 `{"alert_type": "sql_injection", "severity": "high"}` 后，再用第二个 skill 检索 SOP：

```bash
python scripts/kb.py search \
  --path ./data/security_rules \
  --query "sql_injection 高危" \
  --top-k 3
```

两个 skill 串联使用：第一个把非结构化文本变成结构化数据，第二个用结构化数据检索关联知识。

## 距离阈值和相似度评分说明

ChromaDB 返回的是 L2 距离，越小越相似。脚本内部做了两层处理：

1. 阈值过滤：距离超过 threshold（默认 1.5）的结果不返回，避免不相关的硬凑结果
2. 相似度转换：距离转成 0-100 分，distance=0 时 100 分，distance=阈值时 0 分

调整 threshold：
- 想要更严格（只返回高度相关的）：`--threshold 1.0`
- 想要更宽松（多返回一些边缘相关的）：`--threshold 2.0`
