# 向量知识库管理 + 语义检索

## 这是什么

一个本地向量知识库的管理 skill。基于 ChromaDB + sentence-transformers，提供知识条目的增删改查、软删除/恢复、语义检索（带距离阈值过滤和相似度评分）、热更新（写入即生效，无需重启）。解决的核心问题：任何需要语义检索知识的场景都要从零搭一遍向量库 + Embedding + CRUD，重复且容易出错。

## 什么时候触发

当用户需要做以下事情时触发：
- 语义检索（"用户输入问题，找到最相关的知识/FAQ/规则"）
- 知识库管理（增删改查知识条目，需要热更新）
- 相似度匹配（"找和这段文本最相似的 N 条记录"）
- 任何"文本 → 向量 → 检索 → 排序"的场景

## 两种使用方式

### 方式一：直接运行脚本操作知识库（不需要给用户项目写代码）

通过 `scripts/kb.py` 提供完整的 CLI 命令：

```bash
# 初始化知识库（指定存储目录）
python scripts/kb.py init --path ./data/my_kb

# 添加知识条目
python scripts/kb.py add \
  --path ./data/my_kb \
  --type faq \
  --title "MySQL连接超时排查" \
  --content "检查max_connections参数和网络连通性" \
  --tags "mysql,超时"

# 语义检索（带相似度评分和阈值过滤）
python scripts/kb.py search \
  --path ./data/my_kb \
  --query "数据库连不上" \
  --top-k 3

# 列出全部知识
python scripts/kb.py list --path ./data/my_kb

# 编辑知识条目
python scripts/kb.py update \
  --path ./data/my_kb \
  --id <uuid> \
  --title "更新后的标题" \
  --content "更新后的内容" \
  --tags "tag1,tag2"

# 禁用/启用（软删除/恢复）
python scripts/kb.py status --path ./data/my_kb --id <uuid> --status inactive

# 删除（硬删除）
python scripts/kb.py delete --path ./data/my_kb --id <uuid>
```

参数说明：
- `--path`：知识库存储目录。用户指定，或 agent 从用户项目结构推断（通常在项目的 data/ 目录下）。每次运行必须提供。
- `--type`：知识类型，用户自定义（如 faq、rule、article、sop）。
- `--title` / `--content`：知识标题和内容，拼接后整体向量化。
- `--tags`：标签，逗号分隔，可选。
- `--query`：检索文本。
- `--top-k`：返回条数，默认 3。
- `--threshold`：距离阈值，默认 1.5。距离超过阈值的结果不返回。
- `--status`：active 或 inactive。

### 方式二：生成代码集成到用户项目

当用户需要在自己的项目里集成知识库能力时，按以下步骤：

1. 把 `scripts/kb.py` 复制到用户项目目录
2. 在代码中 `from kb import VectorKB` 导入
3. 实例化 `VectorKB(path="./data/my_kb")`
4. 调用 `add()` / `search()` / `update()` / `delete()` / `update_status()` / `list_all()`

生成的代码模板见 `references/examples.md`。

## 核心设计说明

**双写策略**：知识元数据存 JSON 文件（持久化备份），向量数据存 ChromaDB（检索用）。添加时双写，删除时双删，更新时先删后加。

**热更新**：写入 ChromaDB 后立即生效，无需重启服务或刷新缓存。

**软删除/恢复**：通过 status 字段（active/inactive）控制。检索时只返回 status=active 的条目。软删除用"先删后加"策略更新 ChromaDB 的 metadata。硬删除才会物理移除。

**距离阈值过滤**：ChromaDB 的 query 无论输入什么都会返回 Top-K 结果，哪怕是乱码也会硬凑。通过距离阈值过滤掉不相关的结果，避免误导用户。

**相似度评分**：把 ChromaDB 返回的 L2 距离转成 0-100 的相似度评分（distance=0 时 100 分，distance=阈值时 0 分），用户容易理解。结果按相似度从高到低排序。

## 关键注意事项

- 依赖 chromadb 和 sentence-transformers，运行前确认用户环境已安装
- Embedding 模型用 all-MiniLM-L6-v2（384维），首次运行会自动下载（约 80MB）
- `--path` 目录如果不存在会自动创建
- 首次 init 会加载 Embedding 模型，需要几秒钟
- 知识库数据完全本地，不依赖任何外部服务
- 多个知识库用不同的 `--path` 隔离，互不影响
