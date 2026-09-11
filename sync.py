#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 GitHub 星标仓库 -> 分类 README。

用法:
    python sync.py                # 用当前 gh 登录账号的星标(含私有星标)
    STAR_SOURCE=public python sync.py   # 用公开接口 /users/<owner>/starred(供 GitHub Actions 使用)

依赖: gh (GitHub CLI, 已登录) 或 GH_TOKEN 环境变量。
输出: README.md 与 data/starred.json, 均为自动生成, 请勿手改。
"""

import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OWNER = os.environ.get("STAR_OWNER", "Mineocean")
SOURCE = os.environ.get("STAR_SOURCE", "me")
ZH_PATH = ROOT / "i18n" / "zh.json"
CJK = re.compile(r"[\u4e00-\u9fff]")

# ---------------------------------------------------------------- 分类定义
# (key, 标题, 图标, 显式归属的仓库列表)  —— 顺序即 README 中的展示顺序
CATEGORIES = [
    ("dsh", "DeepSeek Harness 生态", "🧩", [
        "MerZlin/dsh-pet-indesktop", "zhu1090093659/dsh-web", "beancookie/awesome-dsh-plugin",
        "libukai/awesome-deepseek-harness", "anywhere-labs/dsh-desktop", "nexu-io/open-design",
        "QwenLM/Qwen-MM-Plugins", "PriceNing/LLM-AIO-Gateway",
    ]),
    ("agent", "AI 编码 Agent / 终端", "🤖", [
        "esengine/DeepSeek-Reasonix", "anomalyco/opencode", "awesome-opencode/awesome-opencode",
        "Hmbown/Codewhale", "colbymchenry/codegraph", "code-yeongyu/oh-my-openagent",
    ]),
    ("mcp", "MCP 服务与工具集成", "🔌", [
        "microsoft/playwright-mcp", "drfccv/mcp-server-12306", "ahujasid/blender-mcp",
    ]),
    ("skills", "Skills / Prompt / AI 输出质量", "🎯", [
        "emilkowalski/skills", "mattpocock/skills", "obra/superpowers", "hardikpandya/stop-slop",
        "Leonxlnx/taste-skill", "linshenkx/prompt-optimizer", "syvixor/skills-icons",
    ]),
    ("aiapp", "AI 应用：生成 / 伴侣 / 平台", "✨", [
        "harry0703/MoneyPrinterTurbo", "Anionex/banana-slides", "Open-LLM-VTuber/Open-LLM-VTuber",
        "moeru-ai/airi", "heshengtao/super-agent-party", "AstrBotDevs/AstrBot",
        "AAswordman/Operit", "liseami/DeepRant", "zyf2007/ChatAPI",
        "victorchen96/deepseek_v4_rolepaly_instruct",
    ]),
    ("nlp", "AI 翻译与文本处理", "🌐", [
        "niedev/RTranslator", "shinnpuru/VoiceTransl", "zyddnys/manga-image-translator",
        "SakuraLLM/SakuraLLM", "royal12646/Chinese-offensive-language-detect",
    ]),
    ("learn", "学习 / 教程 / 科研", "📚", [
        "AccumulateMore/CV", "microsoft/AI-For-Beginners", "datawhalechina/llm-cookbook",
        "CyC2018/CS-Notes", "PKUFlyingPig/cs-self-learning", "0voice/introduce_c-cpp_manual",
        "tradecatlabs/vibe-coding-cn", "ByteLegend/ByteLegend", "yzr278892/arxiv-daily-researcher",
    ]),
    ("digest", "周刊 / Awesome / 资源导航", "📰", [
        "ruanyf/weekly", "521xueweihan/HelloGitHub", "GitHubDaily/GitHubDaily",
        "weekend-project-space/top-rss-list",
    ]),
    ("proxy", "网络代理 / 规则 / 去广告", "🛡️", [
        "powerfullz/override-rules", "INKCR0W/sparkle", "xishang0128/sparkle",
        "getsurfboard/surfboard", "TG-Twilight/AWAvenue-Ads-Rule", "217heidai/adblockfilters",
        "mihomo-party-org/clash-party", "libnyanpasu/clash-nyanpasu", "Loyalsoldier/clash-rules",
        "clash-verge-rev/clash-verge-rev", "GUI-for-Cores/GUI.for.Clash",
        "Loyalsoldier/v2ray-rules-dat", "SukkaW/Surge",
    ]),
    ("media", "音乐 / 影音播放", "🎵", [
        "cwuom/NeriPlayer", "qier222/YesPlayMusic", "HyPlayer/HyPlayer", "Sherlockouo/music",
        "SPlayer-Dev/SPlayer", "WXRIW/Lyricify-App", "lizongying/my-tv", "hooke007/mpv_PlayKit",
        "AlkaidLab/foundation-sunshine", "NewOrin/TVBox", "metowolf/Meting-API",
        "awesome-jellyfin/awesome-jellyfin",
    ]),
    ("anime", "动漫 / 漫画 / 轻小说 / 阅读", "📖", [
        "mihonapp/mihon", "RuliaReader/Rulia", "deretame/Breeze", "SchneeHertz/exhentai-manga-manager",
        "hymbz/ComicReadScript", "Tsuk1ko/nhentai-helper", "open-ani/animeko", "JimHans/bgm.res",
        "wushuo894/ani-rss", "freeok/so-novel", "dmzz-yyhyy/LightNovelReader", "15dd/wenku8reader",
        "MewX/light-novel-library_Wenku8_Android", "montaro2017/bili_novel_packer",
        "sdyzjx/open-yachiyo", "Pixeval/Pixeval", "ZGQ-inc/source",
    ]),
    ("bili", "B站 / 知乎等平台增强", "📺", [
        "the1812/Bilibili-Evolved", "keleus/BewlyCat", "VentusUta/BewlyBewly-AveMujica",
        "bggRGjQaUbCoE/PiliPlus", "orz12/PiliPalaX", "LifeArchiveProject/BiliHistoryFrontend",
        "AHCorn/Bilibili-Batch-Unsubscribe", "ahaduoduoduo/bilibili-youtube-danmaku",
        "Violiate/bili_ticket_rush", "zly2006/zhihu-plus-plus",
    ]),
    ("win", "Windows 桌面效率工具", "🪟", [
        "Kami958/WhoShitsonMyC", "aakk007/RogueCleaner", "Ruben2776/PicView",
        "Flow-Launcher/Flow.Launcher", "vicinaehq/vicinae", "EcoPasteHub/EcoPaste",
        "w4po/ExplorerTabUtility", "seerge/g-helper", "M2Team/NanaZip",
        "std-microblock/breeze-shell", "ShirasawaSama/CefDetectorX",
        "massgravel/Microsoft-Activation-Scripts", "rustdesk/rustdesk", "dudor/BookmarkHub",
    ]),
    ("android", "安卓 / 系统折腾", "📱", [
        "thedjchi/Shizuku", "dadaewq/Install-Lion", "Lin-arm/GKD_subscription",
        "MlgmXyysd/Xiaomi-BootLoader-Questionnaire", "jizizr/signaldock",
        "std-microblock/better-gameviewer", "Ayndpa/ConnectTool",
    ]),
    ("pet", "桌宠 / 趣味", "🐾", [
        "ayangweb/BongoCat", "runcat-dev/RunCat365", "LemonQu-GIT/MurasamePet",
        "Cicada000/VV", "Cute-Dress/Dress", "ayangweb/Awesome-BongoCat",
    ]),
    ("game", "游戏", "🎮", [
        "Meloong-Git/PCL", "PCL-Community/PCL-CE", "BakaXL-Launcher/BakaXL", "teaSummer/MCiSEE",
        "AnYiEE/touhou-mystia-izakaya-assistant", "JK-Block-Arena/The-Datapack",
        "palmcivet/awesome-arknights-endfield", "YumeYucca/YumeBox", "MetaCubeX/mihomo",
    ]),
    ("campus", "校园 / 课程自动化", "🎓", [
        "openschoolcn/zfn_api", "VermiIIi0n/fuckZHS", "Duster-Cule/UnipusHelperPro",
        "FoliageOwO/QingJiaoHelper", "MuQY1818/ChaoXing_Code_Paste",
        "CollegesChat/university-information", "Ac-Wiki/Ac-Wiki",
    ]),
    ("font", "字体 / 排版 / 输入法", "🔤", [
        "lxgw/LxgwZhenKai", "lxgw/LxgwWenKai", "be5invis/Sarasa-Gothic", "subframe7536/maple-font",
        "chenh96/yahei-sarasa", "Warren2060/ChillDuanHeiSong", "iDvel/rime-ice",
    ]),
    ("selfhost", "自建服务 / 开发小工具", "🔧", [
        "openRin/Rin", "MarSeventh/CloudFlare-ImgBed", "UeCook/Short_NURL",
        "donlon/cloudflare-error-page", "groupultra/telegram-search", "quackduck/devzat",
        "YYsuni/2025-blog-public", "XIU2/TrackersListCollection", "LC044/WeChatMsg",
        "motiondivision/motion", "SaekiRaku/vscode-rainbow-fart",
    ]),
    ("privacy", "隐私 / 浏览器 / 安全", "🔒", [
        "fork-maintainers/iceraven-browser", "yokoffing/Betterfox", "stratumauth/app",
    ]),
    ("life", "生活 / 杂项", "🍜", [
        "Anduin2017/HowToCook", "Gar-b-age/CookLikeHOC", "SpaceTheme/Steam",
        "zclllyybb/lofisu-identity-engine",
    ]),
]

# 新星标仓库的关键词兜底规则(按顺序匹配 name + description + topics, 命中即归类)
RULES = [
    ("proxy", r"clash|mihomo|v2ray|sing-box|surge|adblock|广告规则|rule-set|override-rules|机场|订阅节点"),
    ("dsh", r"deepseek[\s-]?harness|\bdsh\b|dsh[-_]"),
    ("mcp", r"\bmcp\b"),
    ("skills", r"agentic skills|skill file|prompt[- ]?(optimiz|engineer)|\bskills\b"),
    ("agent", r"coding agent|code agent|claude code|codex|opencode|cursor|终端.*agent"),
    ("anime", r"漫画|manga|anime|番剧|轻小说|comic|bangumi|pixiv|galgame|追番|小说"),
    ("font", r"字体|font|typeface|输入法|rime"),
    ("media", r"播放器|music|player|歌词|lyric|影音|media server|jellyfin|emby|navidrome|电视直播|iptv"),
    ("bili", r"bilibili|哔哩|b站|zhihu|知乎"),
    ("game", r"minecraft|启动器|datapack|arknights|明日方舟|游戏|game"),
    ("campus", r"教务|超星|智慧树|u校园|青骄|校园|网课|大学英语"),
    ("android", r"android|magisk|shizuku|xposed|hyperos|miui|bootloader|apk"),
    ("win", r"windows|任务栏|右键菜单|剪贴板|clipboard|explorer|文件管理器|7-zip|快捷启动|launcher"),
    ("privacy", r"privacy|隐私|2fa|browser|浏览器|firefox"),
    ("pet", r"桌宠|desktop pet|bongo|桌宠|桌面上养"),
    ("nlp", r"translat|翻译|tts|asr|语音|字幕"),
    ("aiapp", r"\bllm\b|大模型|\bai\b|gpt|agent|多模态"),
    ("selfhost", r"cloudflare|serverless|self-?host|docker|blog|短链|图床|telegram"),
    ("learn", r"教程|tutorial|学习|笔记|course|guide|awesome|自学|面试"),
]

CAT_TITLES = {k: (t, i) for k, t, i, _ in CATEGORIES}
UNCLASSIFIED = ("__new__", "未分类（新星标，等待归位）", "🆕")


# ---------------------------------------------------------------- 抓取
def fetch() -> list:
    endpoint = "user/starred" if SOURCE == "me" else f"users/{OWNER}/starred"
    cmd = ["gh", "api", endpoint, "--paginate", "--jq", ".[] | @json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        sys.exit(f"抓取失败 ({' '.join(cmd)}):\n{proc.stderr.strip()}")
    repos = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    if not repos:
        sys.exit("没有抓到任何星标仓库, 已中止以免把 README 清空。")
    return repos


def classify(repo: dict, explicit: dict) -> str:
    name = repo["full_name"]
    if name in explicit:
        return explicit[name]
    hay = " ".join([
        name,
        repo.get("description") or "",
        " ".join(repo.get("topics") or []),
    ]).lower()
    for key, pattern in RULES:
        if re.search(pattern, hay):
            return key
    return "__new__"


def load_zh() -> dict:
    """英文简介的中文翻译表(可选)。"""
    if not ZH_PATH.exists():
        return {}
    data = json.loads(ZH_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_") and v}


KEEP_FIELDS = (
    "full_name", "html_url", "description", "language", "stargazers_count",
    "forks_count", "topics", "archived", "fork", "created_at", "pushed_at", "license",
)


def slim(repo: dict) -> dict:
    """只保留清单用得到的字段。

    starred 接口里的 permissions 等字段会随抓取身份(带 token 与否)而变,
    留着会让本地与 CI 的快照互相打架, 每次同步都产生大片假 diff。
    """
    out = {}
    for key in KEEP_FIELDS:
        value = repo.get(key)
        if key == "license" and isinstance(value, dict):
            value = value.get("spdx_id")
        out[key] = value
    return out


def describe(repo: dict, zh: dict) -> str:
    """优先用中文译文, 否则用仓库原文。"""
    translated = zh.get(repo["full_name"])
    if translated:
        return esc(translated)
    return esc(repo.get("description")) or "—"


def untranslated(repos: list, zh: dict) -> list:
    """列出了带英文简介、但还没有中文译文的仓库。"""
    return [
        r["full_name"]
        for r in sorted(repos, key=lambda x: -x["stargazers_count"])
        if r.get("description") and not CJK.search(r["description"]) and r["full_name"] not in zh
    ]


# ---------------------------------------------------------------- 渲染
def esc(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def build_readme(repos: list, grouped: dict, zh: dict, now: str) -> str:
    total = len(repos)
    stars = sum(r["stargazers_count"] for r in repos)
    langs = {}
    for r in repos:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    top_langs = ", ".join(f"{k} {v}" for k, v in sorted(langs.items(), key=lambda x: -x[1])[:6])
    zh_hits = sum(1 for r in repos if r["full_name"] in zh)

    order = [k for k, _, _, _ in CATEGORIES] + ["__new__"]
    out = [
        "# ⭐ 我的 GitHub 星标清单",
        "",
        f"> 共 **{total}** 个仓库 · 合计 **{stars:,}** 星 · 主要语言：{top_langs}",
        f"> 最近同步：{now} · 由 [`sync.py`](sync.py) 自动生成，**请勿手动编辑本文件**",
        f"> 其中 **{zh_hits}** 个仓库的英文简介已译为中文（见 [`i18n/zh.json`](i18n/zh.json)）",
        "",
        f"在线查看：[github.com/{OWNER}?tab=stars](https://github.com/{OWNER}?tab=stars)",
        "",
        "## 目录",
        "",
    ]
    for key in order:
        if not grouped.get(key):
            continue
        title, icon = CAT_TITLES.get(key, UNCLASSIFIED)[0], CAT_TITLES.get(key, UNCLASSIFIED)[1]
        out.append(f"- [{icon} {title}](#{key}) — {len(grouped[key])} 个")
    out.append("")

    for key in order:
        items = grouped.get(key)
        if not items:
            continue
        title, icon = CAT_TITLES.get(key, UNCLASSIFIED)[0], CAT_TITLES.get(key, UNCLASSIFIED)[1]
        out.append(f'<a id="{key}"></a>')
        out.append("")
        out.append(f"## {icon} {title} ({len(items)})")
        out.append("")
        out.append("| 仓库 | ⭐ | 语言 | 简介 |")
        out.append("| --- | ---: | --- | --- |")
        for r in items:
            name = r["full_name"]
            desc = describe(r, zh)
            flags = " 🗄️" if r.get("archived") else ""
            out.append(
                f'| [{name}]({r["html_url"]}){flags} | {r["stargazers_count"]:,} '
                f'| {r.get("language") or "—"} | {desc} |'
            )
        out.append("")

    out += [
        "---",
        "",
        "## 如何同步",
        "",
        "```bash",
        "python sync.py                 # 用本机 gh 登录账号抓取(含私有星标)",
        "STAR_SOURCE=public python sync.py   # 走公开接口, 供 CI 使用",
        "```",
        "",
        "- 分类的显式归属写在 `sync.py` 的 `CATEGORIES` 里；新星标会被关键词规则自动归位，",
        "  兜底不中则落到「未分类」，下次同步时把它挪到合适的分类即可。",
        "- 英文简介的中文翻译放在 `i18n/zh.json`（键为 `owner/repo`），有译文的优先显示译文；",
        "  `python sync.py --check` 会列出还没翻译的仓库。",
        "- `.github/workflows/sync.yml` 每天自动跑一次并提交变更（公开星标）。",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    repos = fetch()
    zh = load_zh()

    if "--check" in sys.argv:
        missing = untranslated(repos, zh)
        print(f"已翻译 {sum(1 for r in repos if r['full_name'] in zh)} 个 / 星标共 {len(repos)} 个")
        if missing:
            print(f"\n以下 {len(missing)} 个仓库还是英文简介，可补进 i18n/zh.json：")
            for name in missing:
                print("  " + name)
        else:
            print("英文简介已全部翻译 ✅")
        return

    explicit = {name: key for key, _, _, names in CATEGORIES for name in names}
    grouped = {}
    for repo in repos:
        grouped.setdefault(classify(repo, explicit), []).append(repo)
    for items in grouped.values():
        items.sort(key=lambda r: (-r["stargazers_count"], r["full_name"].lower()))

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "starred.json").write_text(
        json.dumps([slim(r) for r in repos], ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    readme = ROOT / "README.md"
    text = build_readme(repos, grouped, zh, now)
    if readme.exists():
        # 内容没变时保留原时间戳, 避免每天产生只有时间戳变化的噪音提交
        prev = readme.read_text(encoding="utf-8", newline="\n")
        stamp = re.compile(r"最近同步：[^·]+·")
        if stamp.search(prev) and stamp.sub("最近同步：T·", prev) == stamp.sub("最近同步：T·", text):
            text = prev
    readme.write_text(text, encoding="utf-8", newline="\n")

    print(f"共 {len(repos)} 个星标仓库, 其中 {sum(1 for r in repos if r['full_name'] in zh)} 个简介已中文化")
    for key, items in sorted(grouped.items(), key=lambda x: -len(x[1])):
        title = CAT_TITLES.get(key, UNCLASSIFIED)[0]
        print(f"  {len(items):>3}  {title}")


if __name__ == "__main__":
    main()
