# haili-auto-mkt

可复用的 Claude Code / Codex 营销外联工作流技能集。

[English README](./README.md)

## 仓库内容

| 技能 | 用途 | 运行环境 |
|---|---|---|
| `brevo` | 通过 Brevo API 起草、空跑、测试发送、正式发送外联邮件。一封一发，每次都有审计日志。 | Brevo HTTP API |
| `lark` | 读写 Lark / 飞书国际版的文档、表格、云盘、消息。自带 `LarkClient` 库 + OAuth 助手 + JSON 推到 sheet 的脚本。 | Lark 开放平台 API |
| `lark-blog` | 把 Markdown 博客草稿（含 inline 图片占位）转成新的 Lark docx 供审阅。分批 push blocks、上传 PNG、绑定到图片 block。 | Lark 开放平台 API（依赖 `lark` 技能）|
| `luma-event-promo` | Luma 活动从无到有的整套流程：调研同城同类活动、起草不像 AI 写的英文文案、建 Private 草稿、用 admin API 修 start_at / duration / capacity 的坑、调主题字体封面。 | Luma admin API + 浏览器 UI |
| `ph` | Product Hunt 日常养号：拉日榜、按主题分组、推荐跨品类 upvote 目标，让账号看起来像有好奇心的真实用户而不是单一垂类的投票机。 | Product Hunt GraphQL API |
| `xhs-dm` | 驱动桌面版小红书 (Rednote) 完成每日 DM 节奏：从队列里挑 N 个目标，搜索、点赞、关注、发私信、回写结果。 | macOS 桌面应用 + computer-use |

每个技能都是自包含的：一份给 Claude / Codex 读的 `SKILL.md`，
`scripts/` 里的脚本，`references/` 里的参考文档，以及 `templates/` /
`examples/` 里供你填空的模板。

## 三者怎么联动

Python 层面三个技能互相独立（不跨目录 import），但设计上可以靠 agent
串成工作流。常见的联动链路：

| 链路 | 流程 |
|---|---|
| `lark` → `brevo` | 从 Lark 文档或表格里读定稿外联文案 + 收件人，agent 按收件人拼出 Brevo request JSON，`brevo` 空跑 + 测试 + 正式发送。 |
| `xhs-dm` → `lark` | `pick_today.py` 选完目标、DM 跑完之后，agent 调 `LarkClient.update_sheet_values` 在源表上把状态列打勾，让 Lark tracker 和 `queue.json` 同步。 |
| 草稿 → `lark-blog` → 审稿人 | 作者写完 Markdown 博客草稿；`lark-blog` 推成 Lark docx 含 inline 图片；审稿人在 Lark 里评论；定稿后作者手工发到 CMS。 |
| `lark` → `xhs-dm` | agent 用 `LarkClient.get_sheet_values` 从 Lark 表读博主名单，转成 `queue.json` 结构，交给 `xhs-dm` 处理。 |
| `brevo` + `xhs-dm` | 先跑 `brevo` 邮件外联，过一段时间未回复的 agent 自动转进 `xhs-dm` 的 queue.json，走第二条触达渠道。 |

这些链路由 agent 读各自的 `SKILL.md` + references 后串起来，repo 里暂时
没有 glue 脚本。如果某条链路用得多，自然下一步是在目标侧 skill 下加
一个小 driver。

## 一行安装

复制下面这句话发给 Claude Code 或 Codex：

```text
Install haili-auto-mkt from https://raw.githubusercontent.com/Haili321/haili-auto-mkt/main/install.sh into the default skills dir for the current agent, then run a health check.
```

或者自己跑安装脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/Haili321/haili-auto-mkt/main/install.sh | bash
```

安装脚本把 `skills/` 下的每个子目录拷到
`~/.claude/skills/`（或 Codex 的 `${CODEX_HOME:-~/.codex}/skills/`），
已存在的技能会跳过。可以用 `--agent claude` 或 `--agent codex` 强制指定
目标，用 `--dest /custom/path` 安装到自定义路径。

## 直接命令行使用

不走 agent 也能用。本地 clone 之后：

```bash
cp skills/xhs-dm/templates/queue.example.json ./queue.json
cp skills/xhs-dm/templates/dm-message.example.md ./dm-message.md
# 把两个文件改成你自己的真实目标和文案

python3 skills/xhs-dm/scripts/pick_today.py --queue ./queue.json --count 2
# 然后在 Rednote 里按 SOP 手动执行,或者让 agent 跑
python3 skills/xhs-dm/scripts/mark_sent.py --queue ./queue.json 2 3
```

## 目录结构

```
haili-auto-mkt/
├── install.sh              # 给 Claude Code / Codex 用的一键安装脚本
├── skills/
│   ├── brevo/              # Brevo 邮件发送
│   │   ├── SKILL.md
│   │   ├── scripts/        # run_brevo_email.py + 启动 wrapper
│   │   ├── references/     # 请求 schema
│   │   ├── examples/       # 最小 + 外联请求模板
│   │   └── .env.example
│   ├── lark/               # Lark / 飞书国际版 API
│   │   ├── SKILL.md
│   │   ├── scripts/        # lark_client.py + lark_auth.py + push_to_sheet.py
│   │   ├── references/     # 鉴权 + sheet 使用菜谱
│   │   └── templates/      # lark_config.example.json
│   ├── lark-blog/          # Markdown 博客 -> Lark docx 含 inline 图片
│   │   ├── SKILL.md
│   │   ├── scripts/        # push_blog_to_lark.py
│   │   └── examples/       # sample-blog.md
│   ├── luma-event-promo/   # Luma 活动从无到有发布 + polish
│   │   ├── SKILL.md
│   │   ├── scripts/        # update_event.py + build_description.py
│   │   └── references/     # api-cheatsheet + copy-templates + event styles + gotchas
│   ├── ph/                 # Product Hunt 日常养号
│   │   ├── SKILL.md
│   │   ├── scripts/        # ph_daily.py
│   │   └── templates/      # ph_tokens.example.json
│   └── xhs-dm/             # 小红书桌面 DM 工作流
│       ├── SKILL.md
│       ├── scripts/        # pick_today.py + mark_sent.py
│       ├── references/     # SOP + queue schema
│       └── templates/      # queue + DM 文案示例
├── LICENSE
└── README.md
```

## 设计原则

- 技能以读为主。agent 读 `SKILL.md`，然后调用脚本。状态保存在用户自己的
  `queue.json` 和文案文件里，不进 repo。
- 脚本零依赖：只用 Python 3 标准库，不用建虚拟环境。
- 隐私优先：`.gitignore` 屏蔽了 `queue.json` 和 `dm-message.md`，
  真实目标和外联文案不会进 commit。
- 不内置外部集成 (Lark / Notion / Airtable)。如果想把结果同步到外部
  表格，自己写个 driver 脚本包一层 `mark_sent.py` 就行。

## 许可证

MIT，见 [LICENSE](./LICENSE)。
