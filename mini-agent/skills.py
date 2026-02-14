#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from pathlib import Path

from parse_skill import parse_skill

# 内置Skill: 读取文件内容
def read_file(**kw):
    if 'file_path' not in kw:
        raise ValueError('Missing parameter: file_path')
    file_path = kw['file_path']
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 内置Skill: 写入文件
def write_file(**kw):
    if 'file_path' not in kw:
        raise ValueError('Missing parameter: file_path')
    if 'content' not in kw:
        raise ValueError('Missing parameter: content')
    file_path = kw['file_path']
    content = kw['content']
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 内置Skill: 执行shell命令
def exec_command(**kw):
    if 'command' not in kw:
        raise ValueError('Missing parameter: command')
    command = kw['command']
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
    return {
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr
    }

class Skill:
    def __init__(self, name: str, description: str, tool_call: dict, func: callable):
        self.name = name
        self.description = description
        self.tool_call = tool_call
        self.run = func

    def __str__(self):
        return f'Skill: {self.name}: {self.description}'

class SkillManager:
    '''
    SkillManager用于加载和管理Agent的Skill.

    >>> sm = SkillManager(Path('../skills').resolve()) # doctest: +ELLIPSIS
    skill "file_format_convert" loaded: ...
    skill "hello_world" loaded: ...
    skill "read_file" loaded: ...
    skill "write_file" loaded: ...
    skill "exec_command" loaded: ...
    '''

    def __init__(self, skills_path: Path):
        self._skills = {}
        # 扫描skills目录:
        for entry in sorted(skills_path.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / 'SKILL.md'
            if not skill_md.exists():
                continue
            skill_tool_call = parse_skill(entry)
            template = skill_tool_call.pop('template')
            # 定义动态Skill闭包执行函数:
            def make_run_skill(templ):
                def run_skill(**kw):
                    command = templ.format(**kw)
                    return exec_command(command=command)
                return run_skill
            self._register_skill(skill_tool_call, make_run_skill(template))
        # 加载内置Skill:
        read_file_tool_call = {
            'type': 'function',
            'function': {
                'name': 'read_file',
                'description': 'Read and return the contents of a file.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': 'The path to the file to read'
                        }
                    },
                    'required': ['file_path']
                }
            }
        }
        write_file_tool_call = {
            'type': 'function',
            'function': {
                'name': 'write_file',
                'description': 'Write content to a file.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'file_path': {
                            'type': 'string',
                            'description': 'The path to the file to write to.'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'The content to write to the file.'
                        }
                    },
                    'required': ['file_path', 'content']
                }
            }
        }
        exec_command_tool_call = {
            'type': 'function',
            'function': {
                'name': 'exec_command',
                'description': 'Execute a shell command.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'The command to execute.'
                        }
                    },
                    'required': ['command']
                }
            }
        }
        self._register_skill(read_file_tool_call, read_file)
        self._register_skill(write_file_tool_call, write_file)
        self._register_skill(exec_command_tool_call, exec_command)

    def _register_skill(self, skill_tool_call: dict, func: callable):
        name = skill_tool_call['function']['name']
        description = skill_tool_call['function']['description']
        if name in self._skills:
            raise ValueError(f'Duplicate skill: {name}')
        self._skills[name] = Skill(name, description, skill_tool_call, func)
        print(f'skill "{name}" loaded: {description}')

if __name__ == '__main__':
    import doctest
    doctest.testmod()
