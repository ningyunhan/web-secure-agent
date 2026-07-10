# LLM 结构化输出修正管道

## 这是什么

一个让大模型稳定输出结构化 JSON 的 skill。解决的核心问题：LLM 输出的文本经常不规范（包裹 Markdown、多废话、缺字段、格式错误），导致下游代码解析失败。本 skill 提供一套"调用 LLM → 多层解析修正 → 返回可靠结构化对象"的标准化方法。

## 什么时候触发

当用户需要用 LLM 做以下事情时触发：
- 信息提取（从文本中提取结构化字段，如日志分析、简历解析、工单分类）
- 文本分类（输出类别标签 + 置信度）
- 数据转换（非结构化文本转结构化 JSON）
- 任何"输入文本 → LLM → 输出 JSON"的场景

## 两种使用方式

### 方式一：直接运行脚本拿结果（不需要给用户项目写代码）

当用户只需要一次性分析结果时，直接运行 `scripts/analyze.py`：

```bash
echo "用户输入的文本" | python scripts/analyze.py \
  --system-prompt "你是XXX专家，提取XXX字段，输出JSON" \
  --schema '{"field1":"string","field2":"string","confidence":"number"}'
```

参数说明：
- `--system-prompt`：根据用户需求生成。告诉 LLM 它的角色、要提取什么、输出什么格式。末尾必须加"只输出JSON，不要输出其他内容"。
- `--input`：用户提供的待分析文本。也可以通过 stdin 传入。
- `--schema`：根据用户要求的字段生成。JSON 格式，key 是字段名，value 是类型（string/number/boolean）。
- `--api-key`：从环境变量 `OPENAI_API_KEY` 读取。如果没有，问用户要。
- `--base-url`：从环境变量 `OPENAI_BASE_URL` 读取，默认 `https://api.deepseek.com/v1`。
- `--model`：从环境变量 `LLM_MODEL` 读取，默认 `deepseek-chat`。
- `--temperature`：默认 0.1。信息提取类任务用低温度保证稳定性。

脚本输出标准 JSON 到 stdout，agent 直接拿结果返回给用户。

### 方式二：生成代码集成到用户项目

当用户需要在自己的项目里集成这个能力（如批量处理、持续调用）时，按以下步骤生成代码：

1. 用 Pydantic 定义数据结构（根据用户说的字段设计 Model）
2. 写 System Prompt（末尾加"只输出JSON，不要输出其他内容"）
3. 用 OpenAI SDK 调用 LLM（temperature=0.1）
4. 把 `scripts/fixer.py` 复制到用户项目目录
5. 用 `from fixer import parse_and_fix` 调用修正管道
6. `parse_and_fix(raw_output, ModelClass)` 返回合法的 Pydantic 对象

生成的代码模板见 `references/examples.md`。

## fixer.py 修正管道说明

`parse_and_fix(raw_output, model_class)` 接受两个参数：
- `raw_output`：LLM 返回的原始字符串
- `model_class`：Pydantic Model 类

四层修正逻辑（按顺序执行，任一层成功就跳过后续）：
1. 直接 `json.loads` 解析
2. 去除 Markdown 代码块标记（```json ... ```）后解析
3. 正则提取第一个 `{` 到最后一个 `}` 的内容后解析
4. Pydantic 字段级校验：缺失字段补默认值（str→"unknown", number→0.5, bool→False, None→None），多余字段忽略

返回合法的 Pydantic 对象。如果四层全部失败，返回一个所有字段为默认值的对象，不会抛异常。

## 关键注意事项

- System Prompt 末尾必须加"只输出JSON，不要输出其他内容"，这是减少修正压力的第一道防线
- temperature 设 0.1 而非 0，部分模型 temperature=0 时行为不稳定
- schema 中的字段名用英文，中文字段名容易导致 LLM 输出不一致
- 如果用户的输入文本很长（超过 2000 字），提示用户截取关键部分，既省 token 又提高准确率
- fixer.py 依赖 pydantic（v2），analyze.py 依赖 openai 和 pydantic，运行前确认用户环境已安装
