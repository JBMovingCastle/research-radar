# 故障排查

## `Config not found`

在仓库根目录运行：

```bash
python3 -m research_radar init --preset ci3
```

## `Unsafe repository path`

输出只能写到仓库内。把绝对路径改为 `notes/daily` 这类相对路径。

## OpenAlex显示 `misconfigured`

OpenAlex已启用但缺少密钥：

```bash
export OPENALEX_API_KEY="你的密钥"
python3 -m research_radar doctor
```

不想使用时把 `sources.openalex.enabled` 改为 `false`。

## Semantic Scholar `limited`

这表示共享限流或个人额度受限，不表示没有相关文章。可稍后运行，或设置 `S2_API_KEY`。其他来源仍会继续。

## 日报显示“今日无高置信新增”

依次检查：

1. 来源覆盖是否为 `partial`。
2. `tracks[].queries` 是否过窄。
3. `context_keywords` 与方向关键词是否能同时命中。
4. `selection.minimum_score` 是否过高。
5. `venue_mode` 是否错误设成 `only`。

## 同一天没有重新生成

这是每日唯一性保护。确认确实需要重建后运行：

```bash
python3 -m research_radar run --force
```

## 飞书失败

飞书是可选交付，失败不会影响本地日报。检查 `lark-cli`、登录身份和 `FEISHU_USER_ID`，不要把收件人或凭证写入仓库。
