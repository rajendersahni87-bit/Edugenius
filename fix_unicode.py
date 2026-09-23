"""Fix surrogate pairs in generate_ppt.py by replacing them with safe text."""
import re

with open('generate_ppt.py', 'r', encoding='utf-8', errors='surrogatepass') as f:
    content = f.read()

# Replace literal \uXXXX\uXXXX surrogate pair escape sequences
# These look like: \ud83e\udd16 in the Python source
pattern = re.compile(r'\\ud[89a-f][0-9a-f]{2}\\u[0-9a-f]{4}', re.IGNORECASE)
content = pattern.sub('', content)

# Also strip any actual surrogate or non-BMP characters
cleaned = []
for ch in content:
    cp = ord(ch)
    if 0xD800 <= cp <= 0xDFFF:
        continue
    elif cp > 0xFFFF:
        continue
    else:
        cleaned.append(ch)

result = ''.join(cleaned)

with open('generate_ppt.py', 'w', encoding='utf-8') as f:
    f.write(result)

print("Fixed! Removed all surrogate pairs and non-BMP characters.")
