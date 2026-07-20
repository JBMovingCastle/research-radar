# 快速开始

你可以直接让 Codex 初始化、修改配置和生成日报，也可以自己在命令行操作。对不熟悉命令行的使用者，推荐先用方式一。

## 方式一：直接让 Codex 帮你操作

### 1. 下载并打开正确的文件夹

1. 下载仓库压缩包并解压，或克隆仓库。
2. 在 Codex 中打开解压后的 `research-radar` 文件夹。
3. 确认当前文件夹这一层同时包含 `README.md`、`pyproject.toml` 和 `research_radar/`。

然后直接对 Codex 说：

> 帮我初始化这个 Research Radar，使用 CI3 模板。先检查 Python 版本，然后执行 init 和 doctor。不要跑测试，不要生成日报，不要打开浏览器。发现已有配置时不要覆盖。

初始化完成后，再说：

> 帮我生成今天的研究日报。生成后告诉我日报位置、入选数量，以及哪些来源失败或受限。不要发送飞书。

### 2. 用自然语言改成自己的方向

只要把研究主题、数量、期刊策略和报告读者说明白。例如：

> 帮我修改 Research Radar 配置：项目名称改成“智能建造研究组”；重点方向是建筑机器人、施工安全和数字孪生；每天最多推荐 8 条；重点关注 Automation in Construction；保留其他高相关文章，不要只限定这一本期刊。修改前先读取配置手册，只改相关字段。改完不要运行检索，我自己确认。

也可以先让 Codex 给方案，不立即改文件：

> 帮我增加一个“工程教育与生成式 AI”研究方向。关键词包括 engineering education、generative AI、large language model、AI-assisted learning；帮我设计中英文检索式。先给我看修改方案，我确认后再改配置。

只调整日报数量和写法时，可以说：

> 把今天的日报改成最多 5 条，每条摘要不超过 500 个字符，写作风格面向项目组例会。不要改研究方向和数据源。改完不要运行检索。

Codex 只有在打开本机项目文件夹后，才能读取和修改这台电脑上的配置。是否运行检索、测试、打开浏览器或发送飞书，应在指令中明确说明。

## 方式二：自己手动操作

### 1. 下载并检查 Python

```bash
git clone https://github.com/JBMovingCastle/research-radar.git
cd research-radar
python3 --version
```

需要 Python 3.11+，无需先安装 Python 第三方包。

### 2. 初始化

使用 CI3 默认研究方向：

```bash
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
```

完全不使用 CI3 默认方向时，可以改用空白模板和交互式初始化：

```bash
python3 -m research_radar init --preset blank --interactive
python3 -m research_radar doctor
```

`init` 会生成个人配置及本地输出目录；已有配置时默认拒绝覆盖。`doctor` 中的 `INFO` 表示可选增强未配置，只有 `ERROR` 会阻止相应功能。

### 3. 生成日报

```bash
python3 -m research_radar run
```

同一天重复执行会跳过，避免重复日报。只有明确要重建当天日报时才使用：

```bash
python3 -m research_radar run --force
```

## 个人配置应该改哪个文件

初始化后，项目根目录会出现：

```text
research-radar.config.json
```

个人使用时修改这个文件，不要直接修改 `configs/ci3.json` 或 `configs/blank.json`。后两者是随代码发布的内置模板，修改它们会使个人设置和版本升级混在一起。

至少需要关注：

- `project.name` 与 `project.brief_title`
- `context_keywords`
- `tracks[].name / keywords / queries`
- `target_sources`
- `selection.daily_limit / minimum_score / venue_mode`
- `report`

修改后先检查：

```bash
python3 -m research_radar validate
python3 -m research_radar doctor
```

确认无误后再运行 `python3 -m research_radar run`；只有需要重建已经存在的当天日报时才加 `--force`。完整字段映射、示例和注意事项见[配置手册](CONFIGURATION.md)。

## 在 Obsidian 中查看

直接用 Obsidian 打开仓库根目录，或把 `paths.briefs_dir` 改成仓库内另一个相对目录。系统拒绝写入仓库外路径，这是防止误覆盖文件的安全限制。
