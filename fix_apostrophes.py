import re

# Read the file
with open(r'c:\Users\user\Desktop\Maqola Site\pages\views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all triple-quoted string blocks and unescape apostrophes in them
def fix_triple_quoted(match):
    before = match.group(1)
    triple_content = match.group(2)
    after = match.group(3)
    # Remove escaping of apostrophes inside triple quotes
    fixed_content = triple_content.replace("\\'", "'")
    return before + fixed_content + after

# Pattern to match 'content': '''...'''
pattern = r"('content': ''')(.*?)(''',)"
content = re.sub(pattern, fix_triple_quoted, content, flags=re.DOTALL)

# Write back
with open(r'c:\Users\user\Desktop\Maqola Site\pages\views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed apostrophes in triple-quoted strings!')
