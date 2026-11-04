#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Factory 桌面版界面汉化。

不修改 Factory 安装包。启动时加上 Chromium 远程调试端口，再把词典注入页面。
聊天正文、代码编辑器和输入框不翻译。
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

DEBUG_PORT = 9333

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def tool_dir():
    return os.path.dirname(os.path.abspath(__file__))


def dict_path():
    return os.path.join(tool_dir(), "zh-CN.json")


def roaming_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Factory")


def install_root():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Factory")


def versioned_exe():
    root = install_root()
    apps = []
    if os.path.isdir(root):
        for name in os.listdir(root):
            if name.startswith("app-"):
                exe = os.path.join(root, name, "factory-desktop.exe")
                if os.path.isfile(exe):
                    apps.append(exe)
    if not apps:
        return None
    return sorted(apps)[-1]


def stub_exe():
    path = os.path.join(install_root(), "factory-desktop.exe")
    return path if os.path.isfile(path) else versioned_exe()


def load_dictionary():
    path = dict_path()
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("translations", {})


def dict_mtime():
    try:
        return os.path.getmtime(dict_path())
    except OSError:
        return 0


def read_port_file():
    path = os.path.join(roaming_dir(), "DevToolsActivePort")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            port = handle.readline().strip()
            if port.isdigit():
                return port
    except OSError:
        return None
    return None


def port_is_open(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=0.6) as resp:
            return resp.status == 200
    except Exception:
        return False


def current_port():
    filed = read_port_file()
    if filed and port_is_open(filed):
        return filed
    if port_is_open(DEBUG_PORT):
        return str(DEBUG_PORT)
    return None


def factory_running():
    if sys.platform != "win32":
        return False
    script = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'factory-desktop.exe' } | "
        "Select-Object -ExpandProperty ProcessId"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return False
    return bool(result.stdout.strip())


def launch_factory():
    exe = stub_exe()
    if not exe:
        print("[错误] 没有找到 Factory。请先安装官方桌面版。")
        return False
    workdir = os.path.dirname(versioned_exe() or exe)
    args = [
        exe,
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-allow-origins=*",
    ]
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(args, cwd=workdir, creationflags=flags, close_fds=True)
    print(f"[*] 已启动 Factory，调试端口 {DEBUG_PORT}")
    return True


def ensure_factory():
    port = current_port()
    if port:
        return port
    if factory_running():
        print("[错误] Factory 已在运行，但没有打开调试端口。")
        print("       请先完全退出 Factory，再用本目录的「启动Factory.bat」或桌面上的 Factory 快捷方式打开。")
        return None
    if not launch_factory():
        return None
    for _ in range(40):
        time.sleep(0.5)
        port = current_port()
        if port:
            return port
    print("[错误] Factory 已启动，但 20 秒内没有等到调试端口。")
    return None


def build_js(dict_data):
    dict_json = json.dumps(dict_data, ensure_ascii=False)
    return r"""
(() => {
    const dict = %s;
    window.__factoryZhDict = dict;
    window.__factoryZh = { dict, version: 1, translated: 0, skipped: 0 };

    const SKIP_TAGS = new Set([
        'SCRIPT', 'STYLE', 'CODE', 'PRE', 'KBD', 'SAMP', 'TEXTAREA',
        'NOSCRIPT', 'SVG', 'CANVAS', 'IFRAME', 'MATH', 'INPUT'
    ]);

    function classText(el) {
        const cls = el && el.className;
        return typeof cls === 'string' ? cls : '';
    }

    function isSkipped(el) {
        if (!el || el.nodeType !== 1) return false;
        if (SKIP_TAGS.has(el.tagName)) return true;
        if (el.isContentEditable) return true;
        const testid = el.getAttribute && (el.getAttribute('data-testid') || '');
        if (testid && /markdown-body|message-list|chat-transcript|composer-input|terminal-view/i.test(testid)) return true;
        const cls = classText(el);
        if (/(^|\s)(markdown-body|monaco-editor|cm-editor|cm-content|xterm|ProseMirror)(\s|$)/.test(cls)) return true;
        if (/\b(cm-|mtk|view-line|xterm-)/.test(cls)) return true;
        return false;
    }

    function isContentRoot(el) {
        if (!el || el.nodeType !== 1 || !el.getAttribute) return false;
        const role = el.getAttribute('role') || '';
        if (role === 'log') return true;
        const testid = el.getAttribute('data-testid') || '';
        return /markdown-body|message-list|chat-transcript/i.test(testid);
    }

    const DYNAMIC = [
        [/^Thought for\s+(.+)$/, m => '思考耗时 ' + m[1]],
        [/^Thinking\.\.\.$/, () => '思考中...'],
        [/^Working\.\.\.$/, () => '正在执行...'],
        [/^(\d+)\s+files?\s+changed$/, m => m[1] + ' 个文件已更改'],
        [/^(\d+)\s+files?\s+edited$/, m => m[1] + ' 个文件已编辑'],
        [/^(\d+)\s+minutes?\s+ago$/, m => m[1] + ' 分钟前'],
        [/^(\d+)\s+hours?\s+ago$/, m => m[1] + ' 小时前'],
        [/^(\d+)\s+days?\s+ago$/, m => m[1] + ' 天前'],
        [/^(\d+)\s*(s|m|h|d|w|mo)\s+ago$/, m => {
            const u = { s: '秒', m: '分钟', h: '小时', d: '天', w: '周', mo: '个月' }[m[2]];
            return m[1] + ' ' + u + '前';
        }],
        [/^Resets in\s+(.+)$/i, m => m[1] + '后重置'],
        [/^Show more\s*\((.+)\)$/, m => '显示更多 (' + m[1] + ')'],
        [/^See all\s*\((.+)\)$/, m => '查看全部 (' + m[1] + ')'],
        [/^Step\s+(\d+)\s+of\s+(\d+)$/i, m => '步骤 ' + m[1] + ' / ' + m[2]],
        [/^Loading\s+(.+?)(\.\.\.|…)?$/, m => '正在加载' + named(m[1]) + (m[2] || '')],
        [/^Org Settings \((.+)\)$/, m => '组织设置（' + m[1] + '）'],
        [/^API Keys ·\s*(.+)$/, m => 'API 密钥 · ' + m[1]],
        [/^All integrations ·\s*(.+)$/, m => '全部集成 · ' + m[1]],
        [/^Custom Models ·\s*(.+)$/, m => '自定义模型 · ' + m[1]],
        [/^Built\s+(\d+)\s*([smhdw])\s+ago$/i, m => {
            const u = { s: '秒', m: '分钟', h: '小时', d: '天', w: '周' }[m[2].toLowerCase()];
            return m[1] + ' ' + u + '前构建';
        }],
        [/^Factory default \((.+)\)$/, m => 'Factory 默认（' + m[1] + '）'],
        [/^(.+?) Ultra Fast \(unavailable\)$/, m => m[1] + ' 超快速（不可用）'],
        [/^(.+) \(unavailable\)$/, m => m[1] + '（不可用）'],
        [/^(.+) \[Deprecated\]$/, m => m[1] + '［即将停用］'],
        [/^(.+\d.*) Fast Mode$/, m => m[1] + ' 快速模式'],
        [/^(.+\d.*) Fast$/, m => m[1] + ' 快速'],
        [/^Pick (Light|Dark|System) (.+)$/, m => '选择' + themeWord(m[1]) + named(m[2])],
        [/^Open ([A-Z0-9][^.]{0,60})$/, m => '打开 ' + named(m[1])],
        [/^Configure ([A-Z0-9][^.]{0,60})$/, m => '配置 ' + named(m[1])],
        [/^Copy computer name: (.+)$/, m => '复制计算机名称：' + m[1]],
        [/^Copy ([A-Z0-9][^.]{0,80})$/, m => '复制 ' + named(m[1])],
        [/^Actions for (.+)$/, m => m[1] + ' 的操作'],
        [/^Connect personal (.+) account$/, m => '连接个人 ' + m[1] + ' 账户'],
        [/^Connect (.+) organization$/, m => '连接 ' + m[1] + ' 组织'],
        [/^Allow (.+) for organization$/, m => '为组织启用 ' + m[1]],
        [/^Allow members to connect (.+) for personal tasks\.$/, m => '允许成员连接 ' + m[1] + ' 以处理个人任务。'],
        [/^Give Factory access to repositories in your (.+) organization\.$/, m => '授权 Factory 访问你的 ' + m[1] + ' 组织仓库。'],
        [/^Registered:\s*(.+)$/, m => '已注册：' + m[1]],
        [/^Seen in last 24h:\s*(.+)$/, m => '近 24 小时出现：' + m[1]],
        [/^Never seen:\s*(.+)$/, m => '从未出现：' + m[1]],
        [/^(\d+)%% of registered$/, m => '占已注册的 ' + m[1] + '%%'],
        [/^Update available: (.+?)\. Click to download and restart into the latest version\.?$/, m => '有可用更新：' + m[1] + '。点击下载并重启到最新版本。'],
        [/^This message is appended to all delegation tasks started by (.+)$/, m => '这条说明会附加到由 ' + m[1] + ' 发起的所有委派任务。'],
        [/^Build ([0-9a-f]+)$/i, m => '构建 ' + m[1]],
        [/^(Light|Dark) (.+)$/, m => themeWord(m[1]) + named(m[2])]
    ];

    function named(value) {
        return Object.prototype.hasOwnProperty.call(dict, value) ? dict[value] : value;
    }

    function themeWord(value) {
        return { Light: '浅色', Dark: '深色', System: '跟随系统' }[value] || value;
    }

    function translate(text) {
        if (!text) return null;
        const lead = text.match(/^\s*/)[0];
        const tail = text.match(/\s*$/)[0];
        const core = text.trim().replace(/\s+/g, ' ');
        if (!core || core.length > 420) return null;
        if (/^https?:\/\//.test(core) || /^[\w.+-]+@[\w.-]+$/.test(core)) return null;
        if (/[{}]|^\s*(const|let|var|function|import)\b/.test(core)) return null;
        if (Object.prototype.hasOwnProperty.call(dict, core)) return lead + dict[core] + tail;
        for (const [re, fn] of DYNAMIC) {
            const found = core.match(re);
            if (found) return lead + fn(found) + tail;
        }
        return null;
    }

    const ATTRS = ['placeholder', 'title', 'aria-label', 'data-tooltip', 'alt'];

    function blocked(el, skipSelf) {
        let node = skipSelf && el ? el.parentNode : el;
        let depth = 0;
        while (node && node.nodeType === 1 && depth++ < 14) {
            if (isSkipped(node) || isContentRoot(node)) return true;
            node = node.parentNode;
        }
        return false;
    }

    function handleText(node) {
        const parent = node.parentNode;
        if (!parent || parent.nodeType !== 1 || blocked(parent)) return;
        const out = translate(node.nodeValue);
        if (out !== null && out !== node.nodeValue) {
            node.nodeValue = out;
            window.__factoryZh.translated++;
        }
    }

    function handleAttrs(el) {
        const ownChrome = el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA');
        if (!el || el.nodeType !== 1 || blocked(el, ownChrome)) return;
        for (const name of ATTRS) {
            const value = el.getAttribute && el.getAttribute(name);
            if (!value) continue;
            const out = translate(value);
            if (out !== null && out !== value) {
                el.setAttribute(name, out);
                window.__factoryZh.translated++;
            }
        }
    }

    function walk(node, isRoot) {
        if (!node || node.nodeType === undefined) return;
        if (node.nodeType === 1) {
            if (isSkipped(node)) {
                if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA') handleAttrs(node);
                return;
            }
            if (!isRoot && isContentRoot(node)) {
                window.__factoryZh.skipped++;
                return;
            }
            handleAttrs(node);
        } else if (node.nodeType === 3) {
            handleText(node);
            return;
        }
        for (let child = node.firstChild; child; child = child.nextSibling) walk(child, false);
    }

    window.__factoryZhWalk = () => {
        if (document.body) walk(document.body, true);
    };

    if (document.body) walk(document.body, true);
    else document.addEventListener('DOMContentLoaded', () => walk(document.body, true), { once: true });

    if (window.__factoryZhObserver) window.__factoryZhObserver.disconnect();
    const observer = new MutationObserver(mutations => {
        for (const change of mutations) {
            if (change.type === 'childList') change.addedNodes.forEach(node => walk(node, false));
            else if (change.type === 'characterData') handleText(change.target);
            else if (change.type === 'attributes' && change.target) handleAttrs(change.target);
        }
    });
    const root = document.body || document.documentElement;
    if (root) {
        observer.observe(root, {
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true,
            attributeFilter: ATTRS
        });
        window.__factoryZhObserver = observer;
    }

    if (window.__factoryZhTimer) clearInterval(window.__factoryZhTimer);
    let sweeps = 0;
    window.__factoryZhTimer = setInterval(() => {
        sweeps++;
        window.__factoryZhWalk();
        if (sweeps >= 20) {
            clearInterval(window.__factoryZhTimer);
            window.__factoryZhTimer = null;
        }
    }, 500);

    return JSON.stringify({
        ok: true,
        entries: Object.keys(dict).length,
        translated: window.__factoryZh.translated,
        skipped: window.__factoryZh.skipped
    });
})();
""" % dict_json


async def inject_page(ws_url, dict_data):
    import websockets

    source = build_js(dict_data)
    async with websockets.connect(ws_url, max_size=None, open_timeout=5) as ws:
        try:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await asyncio.wait_for(ws.recv(), timeout=2)
            await ws.send(json.dumps({
                "id": 2,
                "method": "Page.addScriptToEvaluateOnNewDocument",
                "params": {"source": source},
            }))
            await asyncio.wait_for(ws.recv(), timeout=2)
        except Exception:
            pass
        await ws.send(json.dumps({
            "id": 3,
            "method": "Runtime.evaluate",
            "params": {"expression": source, "returnByValue": True},
        }))
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        result = json.loads(raw)
        value = result.get("result", {}).get("result", {}).get("value")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                pass
        return {"ok": True, "translated": 0}


async def page_is_active(ws_url):
    import websockets

    try:
        async with websockets.connect(ws_url, max_size=None, open_timeout=3) as ws:
            await ws.send(json.dumps({
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "!!(window.__factoryZh && window.__factoryZh.translated > 0)",
                    "returnByValue": True,
                },
            }))
            raw = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(raw)
            return bool(data.get("result", {}).get("result", {}).get("value"))
    except Exception:
        return False


async def refresh_walk(ws_url):
    import websockets

    try:
        async with websockets.connect(ws_url, max_size=None, open_timeout=3) as ws:
            await ws.send(json.dumps({
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "window.__factoryZhWalk ? (window.__factoryZhWalk(), true) : false",
                    "returnByValue": True,
                },
            }))
            await asyncio.wait_for(ws.recv(), timeout=2)
    except Exception:
        pass


def pages(port):
    url = f"http://127.0.0.1:{port}/json"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            targets = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    found = []
    for target in targets:
        if target.get("type") != "page":
            continue
        page_url = target.get("url") or ""
        if page_url.startswith("devtools:") or page_url.startswith("chrome-extension:"):
            continue
        if target.get("webSocketDebuggerUrl"):
            found.append(target)
    return found


async def inject_all(dict_data, port):
    ok = False
    for page in pages(port):
        ws_url = page.get("webSocketDebuggerUrl")
        title = page.get("title") or "Factory"
        try:
            info = await inject_page(ws_url, dict_data)
            print(f"[成功] {title}：已替换 {info.get('translated', 0)} 处文案。")
            ok = True
        except Exception as exc:
            print(f"[警告] {title} 注入失败：{exc}")
    if not ok:
        print("[错误] 没有找到可注入的 Factory 窗口。")
    return ok


async def watch(port):
    data = load_dictionary()
    seen = dict_mtime()
    print(f"[*] 汉化守护已启动，词条 {len(data)}，端口 {port}", flush=True)
    ticks = 0
    force = True
    while True:
        try:
            latest = dict_mtime()
            dict_changed = latest > seen
            if dict_changed:
                seen = latest
                data = load_dictionary()
                print(f"[!] 词典已更新，现有 {len(data)} 条。", flush=True)
            live = current_port() or port
            if not port_is_open(live):
                await asyncio.sleep(2)
                continue
            ticks += 1
            for page in pages(live):
                ws_url = page.get("webSocketDebuggerUrl")
                if not ws_url:
                    continue
                if force or dict_changed or not await page_is_active(ws_url):
                    info = await inject_page(ws_url, data)
                    print(f"[+] {page.get('title') or 'Factory'} 已汉化 {info.get('translated', 0)} 处。", flush=True)
                    force = False
                elif ticks % 8 == 0:
                    await refresh_walk(ws_url)
        except Exception:
            pass
        await asyncio.sleep(2)


def shortcut_paths():
    paths = []
    desktop = os.path.join(os.path.expanduser("~"), "Desktop", "Factory.lnk")
    start = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\The San Francisco AI Factory, Inc\Factory.lnk",
    )
    for path in (desktop, start):
        if os.path.isfile(path):
            paths.append(path)
    return paths


def shortcut_backup_name(path):
    return os.path.basename(os.path.dirname(path)) + "-" + os.path.basename(path)


def ps_literal(value):
    return str(value).replace("'", "''")


def launcher_python():
    if sys.platform == "win32":
        pythonw = shutil.which("pythonw")
        if pythonw:
            return pythonw
    return sys.executable


def backup_and_retarget_shortcuts():
    if sys.platform != "win32":
        return
    python = launcher_python()
    script = os.path.abspath(__file__)
    workdir = tool_dir()
    backup_dir = os.path.join(workdir, "shortcut-backups")
    os.makedirs(backup_dir, exist_ok=True)
    for path in shortcut_paths():
        backup = os.path.join(backup_dir, shortcut_backup_name(path))
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
        ps = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{ps_literal(path)}')
$s.TargetPath = '{ps_literal(python)}'
$s.Arguments = '"{ps_literal(script)}" --launch'
$s.WorkingDirectory = '{ps_literal(workdir)}'
$s.WindowStyle = 7
$s.Description = 'Factory 中文界面'
$s.Save()
"""
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            text=True,
        )
        print(f"[*] 快捷方式已指向汉化启动器：{path}")


def restore_shortcuts():
    backup_dir = os.path.join(tool_dir(), "shortcut-backups")
    if not os.path.isdir(backup_dir):
        print("[*] 没有快捷方式备份。")
        return
    for dest in shortcut_paths():
        src = os.path.join(backup_dir, shortcut_backup_name(dest))
        if not os.path.isfile(src):
            continue
        shutil.copy2(src, dest)
        print(f"[*] 已恢复：{dest}")


def stop_watchers():
    if sys.platform != "win32":
        return
    my_pid = os.getpid()
    ps = (
        "Get-CimInstance Win32_Process | "
        f"Where-Object {{ $_.CommandLine -like '*factory_zh.py*' -and $_.ProcessId -ne {my_pid} }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)


def start_watcher():
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    pythonw = shutil.which("pythonw") or sys.executable
    subprocess.Popen(
        [pythonw, os.path.abspath(__file__), "--watch"],
        cwd=tool_dir(),
        creationflags=flags,
        close_fds=True,
    )


def main():
    if "--uninstall" in sys.argv:
        stop_watchers()
        restore_shortcuts()
        print("[*] 已停止汉化守护，并恢复原来的 Factory 快捷方式。重启 Factory 后界面回到英文。")
        return
    if "--setup" in sys.argv or "--install" in sys.argv:
        stop_watchers()
        backup_and_retarget_shortcuts()
        print(f"[*] 词典 {len(load_dictionary())} 条。")
        print("[*] 安装完成。之后用原来的 Factory 图标打开即可。")
        print("    如果 Factory 现在已经开着，请先完全退出，再从快捷方式重新打开。")
        return
    if "--watch" in sys.argv:
        port = current_port()
        asyncio.run(watch(port or str(DEBUG_PORT)))
        return

    data = load_dictionary()
    print(f"[*] 已加载 {len(data)} 条词条。")
    port = ensure_factory()
    if not port:
        sys.exit(1)
    start_watcher()
    deadline = time.time() + 25
    injected = False
    while time.time() < deadline:
        pages_now = pages(port)
        if pages_now:
            injected = asyncio.run(inject_all(data, port))
            if injected:
                break
        time.sleep(1)
    if not injected:
        print("[警告] Factory 已启动，但界面还没准备好。守护进程会在窗口出现后继续注入。")
    else:
        print("[*] 界面汉化已挂上。改 zh-CN.json 后约 2 秒会自动重载。")


if __name__ == "__main__":
    main()
