#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
解析指定目录下的SKILL.md文档并返回skill:

{
    "template": "pandoc -t {output_format} -o {output_file} {input_file}",
    "type": "function",
    "function": {
        "name": "file_format_convert",
        "description": "Use pandoc to convert file",
        "parameters": {
            ...
        }
    }
}

SKILL.md必须包含description和usage描述。
'''

import re
from pathlib import Path

def parse_skill(skill_path: Path) -> dict:
    '''
    读取skill_dir目录的SKILL.md并解析skill
    
    >>> skill = parse_skill(Path('../skills/file_format_convert'))
    >>> skill['template']
    'pandoc -f {input_format} -t {output_format} -o {output_file} {input_file}'
    >>> skill['type']
    'function'
    >>> skill['function']['name']
    'file_format_convert'
    >>> skill['function']['parameters']['required']
    ['input_format', 'output_format', 'output_file', 'input_file']
    '''
    skill_md = skill_path / 'SKILL.md'
    with open(skill_md, 'r', encoding='utf-8') as f:
        md_content = f.read()
    sections = split_markdown_by_titles(md_content)
    if 'usage' not in sections:
        raise ValueError('No usage found in SKILL.md')
    if 'description' not in sections:
        raise ValueError('No description found in SKILL.md')
    description = parse_description(sections['description'])
    skill = parse_usage(sections['usage'])
    skill['function']['name'] = skill_path.name
    skill['function']['description'] = description
    return skill

def split_markdown_by_titles(md_content: str) -> dict:
    '''
    Split markdown text by titles.

    >>> md = '\\n \\n# TITLE \\nSample Skill\\n\\n## usage\\nls {dir}\\nlist files of dir.\\n\\n## Meta \\nCopyright@2026\\nhttps://mini-agent.puppylab.org\\n'
    >>> blocks = split_markdown_by_titles(md)
    >>> blocks['title']
    'Sample Skill'
    >>> blocks['usage']
    'ls {dir}\\nlist files of dir.'
    >>> blocks['meta']
    'Copyright@2026\\nhttps://mini-agent.puppylab.org'
    >>> 'reference' in blocks
    False
    '''
    pattern = r'(?m)^(#{1,5}\s+.+)$'
    parts = re.split(pattern, md_content)
    # parts 的第一个元素可能是标题前的空内容，先剔除
    if parts and not parts[0].strip():
        parts.pop(0)
    sections = {}
    # 步长为2遍历：parts[i]是标题，parts[i+1]是内容
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            # 去掉标题开头的 # 号并清理空白
            title = re.sub(r'^#{1,5}\s+', '', parts[i]).strip().lower()
            content = parts[i+1].strip()
            sections[title] = content
    return sections

def parse_description(description: str) -> str:
    '''
    Parse description section and return as str.

    >>> desc_text = '\\n Use pandoc to convert \\n between the formats \\n'
    >>> parse_description(desc_text)
    'Use pandoc to convert between the formats'
    '''
    # 清理空行并拆分:
    lines = [line.strip() for line in description.split('\n') if line.strip()]
    if not lines:
        raise ValueError("Description section is empty")
    result = ' '.join(lines).strip()
    if not result:
        raise ValueError("Description section is empty")
    return result

def parse_usage(usage: str) -> dict:
    '''
    Parse usage section and return LLM tool_call template.
    
    >>> import json
    >>> usage_text = '\\n pandoc -f {input_format} -t {output_format} -o {output_file} {input_file} \\n - input_format: specify input format, can be asciidoc, html, markdown \\n - output_format: specify output format, can be asciidoc, docx, pdf \\n - output_file: the output file name \\n - input_file: the input file name '
    >>> tool_call = parse_usage(usage_text)
    >>> json.dumps(tool_call)
    '{"template": "pandoc -f {input_format} -t {output_format} -o {output_file} {input_file}", "type": "function", "function": {"parameters": {"type": "object", "properties": {"input_format": {"type": "string", "description": "specify input format, can be asciidoc, html, markdown"}, "output_format": {"type": "string", "description": "specify output format, can be asciidoc, docx, pdf"}, "output_file": {"type": "string", "description": "the output file name"}, "input_file": {"type": "string", "description": "the input file name"}}, "required": ["input_format", "output_format", "output_file", "input_file"]}}}'
    >>> usage_text = '\\n pandoc -f {input_format} -t {output_format} -o {output_file} {input_file} \\n - input_format: specify input format, can be asciidoc, html, markdown \\n - output_format: specify output format, can be asciidoc, docx, pdf \\n - output_file: the output file name '
    >>> parse_usage(usage_text)
    Traceback (most recent call last):
        ...
    ValueError: Missing description for parameter: input_file
    '''
    # 清理空行并拆分:
    lines = [line.strip() for line in usage.split('\n') if line.strip()]
    if not lines:
        raise ValueError("Usage section is empty")

    # 提取第一行作为命令模板:
    command_template = lines[0]

    # 找出模板中所有的占位符, 如{input_file}:
    placeholders = re.findall(r'\{(\w+?)\}', command_template)
    
    # 解析参数描述, 格式为: - key: description
    arg_descriptions = {}
    for line in lines[1:]:
        match = re.match(r'\s*\-\s*(\w+)\s*:\s*(.*)', line)
        if match:
            key, desc = match.groups()
            arg_descriptions[key.strip()] = desc.strip()

    # 校验：确保每个占位符都有对应的描述
    for p in placeholders:
        if p not in arg_descriptions:
            raise ValueError(f'Missing description for parameter: {p}')

    # 构造LLM tool_call:
    properties = {
        key: {'type': 'string', 'description': desc}
        for key, desc in arg_descriptions.items() if key in placeholders
    }

    return {
        'template': command_template,
        'type': 'function',
        'function': {
            'parameters': {
                'type': 'object',
                'properties': properties,
                'required': placeholders
            }
        }
    }

if __name__ == '__main__':
    import doctest
    doctest.testmod()
