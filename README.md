# Factory 界面汉化

Unofficial Simplified Chinese overlay for the Factory desktop app. This repository contains the launcher and the dictionary only. It does not include Factory itself.

非官方工具，与 Factory 及其开发公司 The San Francisco AI Factory, Inc. 无关。

不改安装包，也不改程序文件。官方更新后不用重新打补丁，卸掉后官方文件仍是原样。启动时在本机打开调试端口，把 `zh-CN.json` 注入当前窗口。聊天正文、代码、终端和输入框不会被翻译。模型名、产品名、人名、组织名、网址和快捷键保持原文。

词条大约 900 条，覆盖的是菜单、设置和常用短句。改安装包的全量汉化词条更多，界面覆盖也更大。

## 环境

- Windows
- 已安装官方 Factory 桌面版
- Python 3.10 或更高版本，并且能运行 `python` 和 `pythonw`

## 使用

1. 完全退出 Factory。
2. 双击 `install.bat`。它会安装依赖，并把桌面和开始菜单里的 Factory 快捷方式改成汉化启动器。原来的快捷方式备份在本机的 `shortcut-backups`，这个目录不要提交。
3. 之后照常点 Factory 图标。

Factory 已经开着时，双击 `apply_chinese.bat` 只会在它是用汉化启动器打开的情况下生效。从官方程序直接打开的窗口没有调试端口，需要退出后重开。

调试端口是 `127.0.0.1:9333`，只给本机注入翻译。不要把它暴露到局域网或公网。

## 卸载

双击 `uninstall.bat`。它会停掉汉化进程，并把快捷方式恢复成备份。重新打开 Factory 后界面回到英文。

## 补充翻译

编辑 `zh-CN.json` 里的 `translations`。键名必须和界面上的英文完全一致，包括大小写和标点。保存后，大约 2 秒会更新到已经打开的窗口。

不要加入文件名、路径、模型 ID、密钥或聊天内容。

带数字或名字的句子如果整句对不上，可以留在英文。程序里已经处理了一部分会变化的句子，例如步骤编号、加载提示和「组织设置（名字）」。

## 仓库里有什么

| 文件 | 作用 |
| --- | --- |
| `factory_zh.py` | 启动 Factory、注入词典、看守窗口 |
| `zh-CN.json` | 中文词典 |
| `install.bat` | 安装依赖并改快捷方式 |
| `启动Factory.bat` | 用汉化方式打开 Factory |
| `apply_chinese.bat` | 对已经用调试端口打开的窗口再注入一次 |
| `uninstall.bat` | 恢复原来的快捷方式 |
| `requirements.txt` | Python 依赖 |

## 许可

本仓库的脚本和词典使用 [MIT License](LICENSE)。Factory 程序本身不属于本仓库。

---

## 祈愿 · A Blessing

> 无论你从何而来、持何种信仰，或并无信仰，愿你翻开这个项目时安好。
>
> Whoever you are, wherever you come from, whatever you believe or don't —
> may you be well.

这是一份小小的作品，凝结了作者的时间与心意。愿见到它的人各有所得：

- 愿**使用者**从中获得乐趣与灵感；
- 愿**同行的开发者**在此看到值得借鉴之处，也带走一分善意；
- 愿**素不相识的访客**，今日一切顺遂、心安；
- 愿**取用者**心怀敬意、善加对待——尊重他人的创作，即是善待自己。

愿善意流转，愿创造被珍惜，愿彼此以温柔相待。

---

以下是作者依个人信仰所作的祝祷。它是一份心意，不含任何冒犯之意；
你可随喜诵念，也可静静略过——都很好。

<sub>The following is a personal prayer in the author's own faith. It is offered as
goodwill, not as a claim upon anyone. Read it, skip it — you are equally welcome.</sub>

> 吽玛玛吽呢娑哈
>
> 嗡班扎尔萨埵吽
>
> 唵呼嚧呼嚧社曳穆契娑诃
>
> 唵度宁度宁迦度宁莎诃
>
> 南無阿蜜利多多婆亿娑诃
>
> 南無不动如来

愿此作品得护佑：盗窃、侵夺之念，如冰见日，自然消融；
起此念者，亦愿其早遇善缘、心生惭愧，转而向善，离苦得乐。
不为遮挡一人一事，但愿天下造物者皆得珍重，取用者皆存敬意，
巧夺者回头，失意者释怀，见闻者同沾清净、消除业障。

愿以此微功德，回向十方：
愿众生离贪嗔痴，愿创造与善意生生不息，愿世间少一分相夺、多一分相成。

如有不当，请遮止；若有功德，尽归法界，不敢自专。

