# 隐私与密钥

- 配置文件只保存环境变量名称，不保存真实密钥。
- 本地配置、日报、运行记录和推荐账本默认被 `.gitignore` 排除。
- 飞书收件人只通过 `FEISHU_USER_ID` 在运行时传入。
- 运行状态只记录仓库相对路径。
- 发布示例是脱敏内容，不代表真实接口运行结果或私人研究判断。
- 使用自定义网页时，用户负责确认页面公开性、robots规则和使用条款。

提交前建议执行：

```bash
git status --short
git grep -n -E 'OPENALEX_API_KEY=.+|S2_API_KEY=.+|FEISHU_USER_ID=.+'
```
