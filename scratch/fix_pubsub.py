import glob
import re

def fix_pubsub_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    # Replace subscribe
    new_content = re.sub(r"self\.page\.pubsub\.subscribe\((.*?)\)", r'self.page.pubsub.subscribe_topic("live_update", \1)', new_content)
    # Replace unsubscribe
    new_content = re.sub(r"self\.page\.pubsub\.unsubscribe\((.*?)\)", r'self.page.pubsub.unsubscribe_topic("live_update")', new_content)
    
    # Also fix the signature of on_data_update to accept topic
    new_content = re.sub(r"def on_data_update\(self, msg\):", r"def on_data_update(self, topic, msg):", new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed pubsub in {filepath}")

if __name__ == '__main__':
    files = glob.glob('views/*.py')
    for file in files:
        fix_pubsub_in_file(file)
