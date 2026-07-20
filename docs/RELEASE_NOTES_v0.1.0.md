# Research Radar v0.1.0

首个公开版本面向 CI3 同学，目标是“克隆后先能运行，再按自己的研究方向修改”。

## 快速开始

```bash
git clone https://github.com/JBMovingCastle/research-radar.git
cd research-radar
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
python3 -m research_radar run
```

## 本版本包含

- 七类采集适配器和统一候选模型。
- 关键词、方向、作者、种子论文、期刊/ISSN、RSS、网页与输出目录配置。
- 每日唯一 Markdown 日报、来源状态、去重账本和可选飞书交付。
- 两个 Codex Skills、完整中文教程和脱敏示例。

## 重要边界

- OpenAlex需要免费API key；Semantic Scholar无密钥时可能受到共享限流。
- 接口失败会显示为部分覆盖，不代表没有相关研究。
- 系统不绕过付费墙，也不会把摘要级材料标成全文精读。
