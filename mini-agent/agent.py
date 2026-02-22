#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shlex
import threading
from pathlib import Path
from datetime import datetime

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.widgets import TextArea, RadioList, Frame
from prompt_toolkit.key_binding import KeyBindings

from skills import SkillManager

class MyRadioList(RadioList):
    def __init__(self, *args, on_change=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_change = on_change

    def _handle_enter(self):
        # RadioList 原本的回车逻辑是选中并返回
        # 我们在这里插入自己的回调
        super()._handle_enter()
        if self.on_change:
            self.on_change(self.current_value)

class MiniAgent:
    def __init__(self, workspace: Path = None):
        # 路径初始化:
        self.pwd = Path(__file__).resolve().parent
        self.workspace = workspace or Path("~/.mini-agent-workspace").expanduser()
        self.skills_path = self.pwd.parent / "skills"
        self.workspace.mkdir(exist_ok=True)

        # 组件初始化
        self.skill_manager = SkillManager(self.skills_path)
        #self.session_manager = SessionManager(self.workspace)
        self.current_session = None

        # TUI 组件
        self.task_list = MyRadioList(values=[
            ("task-0", "默认：聊天"),
            ("task-1", "📝 任务: 修复Bug"),
            ("task-2", "🚀 任务: 部署xxx环境"),
            ("task-3", "📝 任务: 修复Bug"),
            ("task-4", "🚀 任务: 部署xxx环境"),
            ("task-5", "📝 任务: 修复Bug"),
            ("task-6", "🚀 任务: 部署xxx环境"),
            ("task-7", "📝 任务: 修复Bug"),
            ("task-8", "🚀 任务: 部署xxx环境"),
            ("task-9", "📝 任务: 修复Bug"),
        ], on_change=self.on_task_changed)

        self.output_field = TextArea(text=r'''
        _       _     _                    _
  /\/\ (_)_ __ (_)   /_\   __ _  ___ _ __ | |_
 /    \| | '_ \| |  //_\\ / _` |/ _ \ '_ \| __|
/ /\/\ \ | | | | | /  _  \ (_| |  __/ | | | |_
\/    \/_|_| |_|_| \_/ \_/\__, |\___|_| |_|\__|
                          |___/
version 0.1
''' + 'Type /help for commands.\n', read_only=True, scrollbar=True)
        self.input_field = TextArea(prompt="> ", multiline=True)
        self.kb = KeyBindings()
        
        # 基础切换逻辑
        @self.kb.add('tab')
        def _(event):
            event.app.layout.focus_next()

        @self.kb.add('enter')
        def _(event):
            raw_input = self.input_field.text.strip()
            self.input_field.text = "" # 清空输入
            
            if not raw_input:
                return

            try:
                parts = shlex.split(raw_input)
                cmd = parts[0].lower()
                args = parts[1:]

                # --- 路由逻辑 ---
                if cmd in ['/exit', '/quit', '/q']:
                    self._handle_exit()
                    event.app.exit()
                elif cmd in ['/help', '/h']:
                    self.append_log("Commands: status, new <task>, pause, stop, help")
                elif cmd in ['/status', '/st']:
                    self._cmd_status()
                elif cmd == 'new':
                    if args: self._cmd_new(args[0])
                    else: self.append_log("Usage: new <task_name>")
                elif cmd in ['/stop', '/s']:
                    self._cmd_stop()
                elif cmd in ['/pause', '/p']:
                    self._cmd_pause()
                else:
                    # 如果不是内置命令，则作为对话处理
                    self._handle_chat(raw_input)

            except Exception as e:
                self.append_log(f"Error: {str(e)}")

    def append_log(self, text: str):
        '''向滚动区域追加文本并滚动到底部'''
        self.output_field.text += f"{text}\n"
        # 自动滚动到底部
        self.output_field.buffer.cursor_position = len(self.output_field.text)

    # --- 命令实现函数 ---
    def on_task_changed(self, value):
        """RadioList选中回调（value是选中的ID，如task-1）"""
        # 查找选中项的显示文本
        selected_label = next((label for val, label in self.task_list.values if val == value), None)
        if selected_label:
            self.append_log(f"\n[🔍 已选中任务]: {selected_label} (ID: {value})")

    def _cmd_new(self, task_name: str):
        date_str = datetime.now().strftime("%Y-%m-%d")
        session_id = f"{date_str}-{task_name}"
        # 这里实例化你写的 Session 类
        # self.current_session = Session(self.sessions_path / session_id)
        self.append_log(f"[*] Started new task: {session_id}")
        self.input_field.prompt = f"[{task_name}] >>> "

    def _cmd_status(self):
        self.append_log(f"{'Session ID':<30} | {'Status':<10}")
        self.append_log("-" * 45)
        for p in sorted(self.sessions_path.iterdir(), reverse=True):
            if p.is_dir():
                # 简单读取 meta.json
                self.append_log(f"{p.name:<30} | ...") 

    def _cmd_stop(self):
        if self.current_session:
            sid = self.current_session.session_id
            # self.current_session.set_status('failed')
            # self.current_session.save()
            self.current_session = None
            self.input_field.prompt = ">>> "
            self.append_log(f"[!] Task {sid} stopped.")
        else:
            self.append_log("No active task to stop.")

    def _handle_chat(self, text: str):
        if not self.current_session:
            self.append_log("[!] No active session. Use 'new <task>' first.")
            #return
        self.append_log(f"👤: {text}")

        # 后台线程调用LLM:
        loop = get_app().loop
        def _background_task():
            import time
            time.sleep(2)
            result = 'hehe, it is ok!'
            # 拿到结果后, UI线程负责更新:
            loop.call_soon_threadsafe(self._finalize_chat, result)
        threading.Thread(target=_background_task, daemon=True).start()

    def _finalize_chat(self, result):
        self.append_log(f"💻: {result}")

    def _handle_exit(self):
        if self.current_session and self.current_session.is_dirty:
            # self.current_session.save()
            pass

    def run(self):
        # 关键修复：使用HSplit包装RadioList，添加填充占满高度
        task_container = HSplit([
            # RadioList 内容
            self.task_list,
            # 填充容器：占满剩余所有空间
            Window(height=D(weight=1))
        ])
        upper_layout = VSplit([
            Frame(self.output_field, title='Log', height=D(weight=1)),
            # 右侧Tasks面板：使用包装后的容器，确保占满高度
            Frame(
                task_container,
                title='Tasks',
                width=25,
                height=D(weight=1)
            )
        ])
        layout = Layout(HSplit([
            upper_layout,
            Frame(self.input_field, title='Input', height=5)
        ]), focused_element=self.input_field)
        
        app = Application(layout=layout, key_bindings=self.kb, full_screen=True)
        app.run()

if __name__ == '__main__':
    agent = MiniAgent()
    agent.run()
