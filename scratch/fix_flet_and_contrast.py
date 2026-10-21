import glob
import re

def fix_flet_api_and_contrast(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Fix padding.all(X) to X
    content = re.sub(r'ft\.padding\.all\(([^)]+)\)', r'\1', content)

    # 2. Fix border.all(width, color)
    def border_all_replacer(match):
        width = match.group(1)
        color = match.group(2)
        return f"ft.Border(top=ft.BorderSide({width}, {color}), right=ft.BorderSide({width}, {color}), bottom=ft.BorderSide({width}, {color}), left=ft.BorderSide({width}, {color}))"
        
    content = re.sub(r'ft\.border\.all\(([^,]+),\s*([^)]+)\)', border_all_replacer, content)

    # 3. Fix colors for better contrast
    content = content.replace("ft.Colors.GREY_400", "ft.Colors.BLUE_GREY_800")
    content = content.replace("ft.Colors.GREY_500", "ft.Colors.BLUE_GREY_800")
    content = content.replace("ft.Colors.GREY_600", "ft.Colors.BLUE_GREY_900")
    content = content.replace("ft.Colors.GREY_700", "ft.Colors.BLUE_GREY_900")
    
    content = content.replace("ft.Colors.BLUE_GREY_400", "ft.Colors.BLUE_GREY_800")
    content = content.replace("ft.Colors.BLUE_GREY_500", "ft.Colors.BLUE_GREY_800")
    content = content.replace("ft.Colors.BLUE_GREY_600", "ft.Colors.BLUE_GREY_900")
    
    # Let's also check for plain GREY
    content = re.sub(r'ft\.Colors\.GREY([^a-zA-Z0-9_])', r'ft.Colors.BLUE_GREY_900\1', content)

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed {filepath}")

for f in glob.glob('/Users/asper/Programming/Flutter UI:UX/erp_demo/views/*.py'):
    fix_flet_api_and_contrast(f)

for f in glob.glob('/Users/asper/Programming/Flutter UI:UX/erp_demo/components/*.py'):
    fix_flet_api_and_contrast(f)

fix_flet_api_and_contrast('/Users/asper/Programming/Flutter UI:UX/erp_demo/main.py')
