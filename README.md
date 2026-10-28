# Classical Astro Natal · 古典占星本命盘分析 Skill

一套面向 AI 编程助手的中文古典占星 Skill，包含主调度指令、10 个专项 Agent、知识库和 Python 排盘工具，覆盖从出生信息采集、星盘计算到专项解读、报告生成与审核的流程。

## 功能范围

| 模块 | 内容 |
| --- | --- |
| 排盘 | 行星位置、十二宫位、四轴、相位及行星状态 |
| 性格画像 | 上升、太阳、月亮与性格层次分析 |
| 事业 | 职业类型、职业环境、事业运势与推运 |
| 财运 | 财运类型、财务环境、运势与推运 |
| 感情 | 桃花、配偶特征、婚姻质量与推运 |
| 健康 | 身体健康、心理健康、意外伤害相关主题与推运 |
| 学业 | 学习领域、科目、学历层次、考试运与推运 |
| 六亲 | 父母、配偶、子女与相关推运 |
| 报告与审核 | 汇总分析、核对数据、检查依据链与表述 |

专项解读要求按照“结论 → 依据 → 含义 → 表现 → 建议”组织内容，报告阶段整合不同领域的分析，审核阶段检查数据一致性、结论依据与表述边界。

## 目录结构

```text
.
├── SKILL.md                     # 主调度入口
├── agents/
│   ├── chart-cast/               # 信息采集与排盘
│   ├── personality-analysis/     # 性格画像
│   ├── career-analysis/          # 事业
│   ├── wealth-analysis/          # 财运
│   ├── relationship-analysis/    # 感情
│   ├── health-analysis/          # 健康
│   ├── education-analysis/       # 学业
│   ├── family-analysis/          # 六亲
│   ├── report-gen/               # 报告生成
│   ├── audit-agent/              # 审核校验
│   └── knowledge/                # Agent 共用输出规范
├── astro-chart/
│   ├── SKILL.md                  # 排盘工具说明
│   └── astro_calc.py             # Swiss Ephemeris 排盘脚本
└── knowledge/                   # 公共方法论、判断规则与推运框架
```

## 开始使用

### 1. 获取仓库

```bash
git clone https://github.com/mooo-hub/astro-skill-261028.git classical-astro-natal
cd classical-astro-natal
```

### 2. 准备运行环境

完整解读需要能够读取本地文件、执行 Python，并支持 Agent 调度的 AI 助手。Python 脚本负责星盘计算，专项解读和报告审核由 AI 助手根据 Skill 指令完成。

安装排盘依赖：

```bash
python -m pip install pyswisseph
python -c "import swisseph as swe; print(swe.version)"
```

### 3. 加载 Skill

将仓库完整放入所用助手的技能目录，并保留 `agents/`、`knowledge/` 和 `astro-chart/` 的相对结构；也可以在项目中直接要求助手读取根目录的 [SKILL.md](SKILL.md)，再按需加载子 Agent 与知识文件。

不同助手的技能发现和子 Agent 注册方式不同，需要按宿主工具配置。仓库中的嵌套 `SKILL.md` 不代表宿主会自动注册所有子 Agent。

部分排盘说明使用 `~/.claude/skills/astro-chart/astro_calc.py` 路径。使用本仓库的嵌套布局时，应改用实际路径，例如在仓库根目录执行 `python astro-chart/astro_calc.py ...`。

### 4. 发起分析

提供公历出生日期、当地出生时间、出生地点，以及想重点讨论的问题。按信息采集要求补充性别等资料。

```text
请读取 SKILL.md，按 classical-astro-natal 流程分析我的本命盘。
出生信息：1997 年 2 月 18 日 13:34，山东东营，UTC+8。
性别：请填写。
重点问题：事业方向、学习发展，以及未来一年的关注事项。
```

执行流程为：信息采集与排盘 → 性格画像 → 确认具体问题 → 专项分析与推运 → 报告生成 → 审核与修订 → 交付。

## 单独使用排盘脚本

在仓库根目录执行，无需启动完整的 AI 解读流程：

```bash
python astro-chart/astro_calc.py 年 月 日 时 分 经度 纬度 [时区] [分宫制] [模式]
```

```bash
# 默认：UTC+8、阿卡比特分宫制、古典占星模式
python astro-chart/astro_calc.py 1997 2 18 13 34 118.5 37.4

# 整宫制，古典占星模式
python astro-chart/astro_calc.py 1997 2 18 13 34 118.5 37.4 8 whole classical

# Placidus 分宫制，现代占星模式
python astro-chart/astro_calc.py 1997 2 18 13 34 118.5 37.4 8 placidus modern
```

| 参数 | 支持值或说明 |
| --- | --- |
| 日期与时间 | 公历年、月、日，以及当地时间的时、分；使用 24 小时制 |
| 经纬度 | 东经、北纬为正，西经、南纬为负 |
| 时区 | 当前命令行实现接受整数 UTC 偏移，默认 `8`；需自行确认出生时当地的夏令时 |
| 分宫制 | `alcabitius`（默认）、`placidus`、`whole`、`koch`、`equal` |
| 模式 | `classical`（默认）或 `modern` |

古典模式使用七大古典行星计算主要相位，并采用 William Lilly 行星容许度；现代模式包含三王星，采用固定相位容许度。切换模式时，可像示例一样明确指定对应分宫制。

脚本输出星盘计算报告及原始 JSON 数据，不会单独生成完整的事业、感情等专项解读。更多细节见 [排盘工具说明](astro-chart/SKILL.md)。

## 进一步阅读

- [主调度流程](SKILL.md)
- [公共知识索引](knowledge/INDEX.md)
- [信息采集与排盘 Agent](agents/chart-cast/SKILL.md)
- [报告生成 Agent](agents/report-gen/SKILL.md)
- [审核 Agent](agents/audit-agent/SKILL.md)
