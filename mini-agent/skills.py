#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Skill:
    def __init__(self, name: str, description: str, func: callable):
        self.name = name
        self.description = description
        self.run = func

# 内置Skill: 读取文件内容
def read_file(self, **kw):
    if 'file_path' not in kw:
        raise ValueError('Missing parameter: file_path')
    file_path = kw['file_path']
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 内置Skill: 写入文件
def write_file(self, **kw):
    if 'file_path' not in kw:
        raise ValueError('Missing parameter: file_path')
    if 'content' not in kw:
        raise ValueError('Missing parameter: content')
    pass

# 内置Skill: 执行shell命令
def exec_command(self, **kw):
    if 'command' not in kw:
        raise ValueError('Missing parameter: command')
    command = kw['command']


class SkillManager:
    def __init__(self, skills_dir: str):
        pass

