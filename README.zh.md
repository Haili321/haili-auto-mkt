# haili-auto-mkt

可复用的 Claude Code / Codex 营销外联工作流技能集。

[English README](./README.md)

## 仓库内容

| 技能 | 用途 | 运行环境 |
|---|---|---|
| `xhs-dm` | 驱动桌面版小红书 (Rednote) 完成每日 DM 节奏：从队列里挑 N 个目标，搜索、点赞、关注、发私信、回写结果。 | macOS 桌面应用 + computer-use |

后续会加更多技能。每个技能都是自包含的：一份给 Claude / Codex 读的
`SKILL.md`，`scripts/` 里的脚本，`references/` 里的参考文档，以及
`templates/` 里的文案模板。

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
│   └── xhs-dm/
│       ├── SKILL.md        # 技能元信息 + 给 agent 的流程说明
│       ├── scripts/
│       │   ├── pick_today.py
│       │   └── mark_sent.py
│       ├── references/
│       │   ├── sop.md
│       │   └── queue-schema.md
│       └── templates/
│           ├── queue.example.json
│           └── dm-message.example.md
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

## 来源

目录结构借鉴了 MIT 许可证的 Yinch Auto MKT 项目
([NetMindAI-Open/yinch-auto-mkt](https://github.com/NetMindAI-Open/yinch-auto-mkt))，
精简为单技能版本，方便 fork 和扩展。

## 许可证

MIT，见 [LICENSE](./LICENSE)。
