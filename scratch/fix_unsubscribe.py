import os
import glob
import re

files = glob.glob('/Users/asper/Programming/Flutter UI:UX/erp_demo/**/*.py', recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    # Replace any `unsubscribe_topic("topic", handler)` with `unsubscribe_topic("topic")`
    new_content = re.sub(r'unsubscribe_topic\("live_update", [^\)]+\)', 'unsubscribe_topic("live_update")', content)
    
    if new_content != content:
        with open(file, 'w') as f:
            f.write(new_content)
        print(f"Updated {file}")
