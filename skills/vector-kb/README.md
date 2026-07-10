# vector-kb

本地向量知识库管理 + 语义检索的 skill。基于 ChromaDB + sentence-transformers。

## 解决什么问题

任何需要语义检索知识的场景（FAQ 检索、规则匹配、文档搜索），都要从零搭一遍向量库 + Embedding + 增删改查 + 软删除 + 距离阈值过滤。这个 skill 把这套重复工作标准化了。

## 文件说明

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 方法论说明，给 AI agent 读取 |
| `scripts/kb.py` | 完整的 VectorKB 类 + CLI 入口，既可作为模块 import，也可命令行直接运行 |
| `references/examples.md` | 四个场景的完整使用示例（运维FAQ、安全规则、文档检索、与第一个skill组合） |

## 两种用法

**命令行直接操作：**

```bash
# 初始化知识库
python scripts/kb.py init --path ./data/my_kb

# 添加知识
python scripts/kb.py add --path ./data/my_kb --type faq --title "标题" --content "内容"

# 语义检索
python scripts/kb.py search --path ./data/my_kb --query "搜索文本" --top-k 3

# 禁用/启用/删除/编辑/列表
python scripts/kb.py status --path ./data/my_kb --id <uuid> --status inactive
python scripts/kb.py delete --path ./data/my_kb --id <uuid>
python scripts/kb.py update --path ./data/my_kb --id <uuid> --type faq --title "新标题" --content "新内容"
python scripts/kb.py list --path ./data/my_kb
```

**集成到项目代码：**

```python
from kb import VectorKB

kb = VectorKB("./data/my_kb")

# 添加（立即生效）
kb.add(type="faq", title="MySQL连接超时", content="检查max_connections...", tags=["mysql"])

# 检索（带相似度评分，按相关度排序）
results = kb.search("数据库连不上", top_k=3)
for r in results:
    print(f"[{r['similarity']}分] {r['title']}")

# 软删除/恢复
kb.update_status(id="abc-123", status="inactive")

# 编辑
kb.update(id="abc-456", type="faq", title="更新标题", content="更新内容")

# 硬删除
kb.delete(id="abc-789")
```

## 核心特性

- 热更新：写入即生效，无需重启
- 软删除/恢复：status 字段控制，检索只返回 active 条目
- 距离阈值过滤：默认 1.5，过滤不相关的硬凑结果
- 相似度评分：L2 距离转 0-100 分，用户直观可读
- 双写策略：JSON 存元数据 + ChromaDB 存向量
- 完全本地：不依赖任何外部服务

## 依赖

- chromadb >= 0.5
- sentence-transformers >= 3.0
- pydantic >= 2.0
