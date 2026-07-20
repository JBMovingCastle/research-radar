# 快速开始

## 1. 下载并检查 Python

```bash
git clone https://github.com/JBMovingCastle/research-radar.git
cd research-radar
python3 --version
```

需要 Python 3.11+，无需先安装 Python 第三方包。

## 2. 初始化

```bash
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
```

`doctor` 中的 `INFO` 表示可选增强未安装；只有 `ERROR` 会阻止相应功能。

## 3. 生成日报

```bash
python3 -m research_radar run
```

同一天重复执行会跳过，避免重复日报。只有明确重建时使用 `--force`。

## 4. 改成自己的方向

打开 `research-radar.config.json`，至少修改：

- `project.name` 与 `project.brief_title`
- `context_keywords`
- `tracks[].name / keywords / queries`
- `target_sources`

保存后执行：

```bash
python3 -m research_radar validate
python3 -m research_radar run --force
```

## 5. 在 Obsidian 中查看

直接用 Obsidian 打开仓库根目录，或把 `paths.briefs_dir` 改成仓库内另一个相对目录。系统拒绝写入仓库外路径，这是防止误覆盖文件的安全限制。
