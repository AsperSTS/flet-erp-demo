import glob
import re

def fix_islands_in_file(filepath):
    # Don't modify dashboard or auth as they handle their own islands
    if 'dashboard.py' in filepath or 'auth.py' in filepath:
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    island_code = """
        self.bgcolor = ft.Colors.WHITE
        self.border_radius = 20
        self.shadow = ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12, spread_radius=1, offset=ft.Offset(0, 5))"""
        
    if "self.bgcolor = ft.Colors.WHITE" not in content:
        new_content = re.sub(
            r"(self\.padding = 24\n)", 
            r"\1" + island_code + "\n", 
            content
        )
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed islands in {filepath}")

if __name__ == '__main__':
    files = glob.glob('views/*.py')
    for file in files:
        fix_islands_in_file(file)
