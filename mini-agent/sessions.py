#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime

from pathlib import Path

# task运行的状态:
RUNNING = 'running'
PAUSED = 'paused'
SUCCESS = 'success'
FAILED = 'failed'

class Session:
    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.session_id = session_path.name
        
        # 定义内部文件路径
        self._meta_path = session_path.joinpath('meta.json')
        self._history_path = session_path.joinpath('history.json')
        self._log_path = session_path.joinpath('session.log')
        
        # 初始化内部状态
        now = self._now()
        self._meta = {
            'name': 'unnamed',
            'status': RUNNING,
            'steps': 0,
            'failures': 0,
            'created_at': now,
            'last_active': now
        }
        if self._meta_path.exists():
            with open(self._meta_path, 'r', encoding='utf-8') as f:
                self._meta.update(json.load(f))

        self._history = None
        
        # 初始化日志记录器
        self._logger = logging.getLogger(self.session_id)
        self._logger.setLevel(logging.INFO)
        
        # 防止重复添加 handler
        if not self._logger.handlers:
            fh = logging.FileHandler(self._log_path, encoding='utf-8')
            formatter = logging.Formatter('---------- %(asctime)s - %(levelname)s ----------\n%(message)s\n')
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)

    def get_meta(self) -> dict:
        return self._meta

    def get_history(self) -> list:
        if self._history is None:
            if self._history_path.exists():
                with open(self._history_path, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            else:
                self._history = []
        return self._history

    def save(self):
        '''持久化 meta 和 history'''
        self._meta['last_active'] = self._now()
        
        # 写入 meta.json
        with open(self._meta_path, 'w', encoding='utf-8') as f:
            json.dump(self._meta, f, indent=2, ensure_ascii=False)    
        # 写入 history.json
        with open(self._history_path, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)

        self._log(f'Session state saved to {self.session_path}', logging.DEBUG)

    def add_message(self, role: str, content: str, failure: bool = False, **kwargs):
        '''添加对话条目'''
        message = {'role': role, 'content': content}
        message.update(kwargs) # 处理 tool_call_id 等扩展字段
        self._history.append(message)
        
        if role == 'assistant':
            self._meta['steps'] += 1
        if failure:
            self._meta['failures'] += 1
        self._log(f'Added message from {role}')

    def _log(self, message: str, level: int = logging.INFO):
        '''记录日志到 session.log'''
        self._logger.log(level, message)

    def _now(self) -> str:
        now = datetime.now()
        now.microsecond = 0
        return now.isoformat()
