import os
import glob
import re

def refactor_view(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
        
    if "IslandLayout" in content:
        return # Already refactored
        
    if "ft.Tabs" not in content:
        return
        
    # Extract tabs
    tab_pattern = r'ft\.Tab\(text="([^"]+)",\s*icon=(ft\.Icons\.[A-Z0-9_]+),\s*content=(self\._build_[a-z0-9_]+)\(\)\)'
    tabs = re.findall(tab_pattern, content)
    
    if not tabs:
        # Try alternate pattern (label instead of text, and separated TabBar/TabBarView)
        label_pattern = r'ft\.Tab\(\s*label="([^"]+)",\s*icon=(ft\.Icons\.[A-Z0-9_]+)\s*\)'
        labels = re.findall(label_pattern, content)
        
        control_pattern = r'self\._build_[a-z0-9_]+\(\)'
        # Extract the TabBarView controls
        tabbarview_match = re.search(r'ft\.TabBarView\([^\[]*controls=\[([^\]]+)\]', content)
        if labels and tabbarview_match:
            controls = re.findall(control_pattern, tabbarview_match.group(1))
            if len(labels) == len(controls):
                tabs = [(l[0], l[1], c) for l, c in zip(labels, controls)]
    
    if not tabs:
        print(f"Could not extract tabs for {file_path}")
        return
        
    # Extract Title and Icon and Color
    title_match = re.search(r'ft\.Text\("([^"]+)",\s*size=26,\s*weight=ft\.FontWeight\.BOLD\)', content)
    title = title_match.group(1) if title_match else "Módulo ERP"
    
    icon_match = re.search(r'ft\.Icon\((ft\.Icons\.[A-Z0-9_]+),\s*size=36,\s*color=(ft\.Colors\.[A-Z0-9_]+)\)', content)
    main_icon = icon_match.group(1) if icon_match else "ft.Icons.APPS"
    main_color = icon_match.group(2) if icon_match else "ft.Colors.BLUE_700"
    
    # Generate Categories code
    cat_code = "        categories = [\n"
    for title_cat, icon_cat, method_cat in tabs:
        # Clean method call
        method_ref = method_cat.replace("()", "")
        cat_code += f'            IslandCategory("{title_cat}", {icon_cat}, {main_color}, "Resumen y Detalles", {method_ref}),\n'
    cat_code += "        ]\n"
    
    layout_code = f"""        self.content = IslandLayout(
            title="{title}",
            icon={main_icon},
            color={main_color},
            categories=categories
        )"""

    # Replace build_ui entirely up to def _build_... or def _table or anything after build_ui
    # We find where build_ui starts
    build_ui_start = content.find("def build_ui(self):")
    if build_ui_start == -1:
        return
        
    # Find next method
    next_method_start = len(content)
    for m in re.finditer(r'\n    def _', content[build_ui_start:]):
        next_method_start = build_ui_start + m.start() + 1
        break
        
    if next_method_start == len(content):
        for m in re.finditer(r'\n    def kpi', content[build_ui_start:]):
            next_method_start = build_ui_start + m.start() + 1
            break

    new_build_ui = "    def build_ui(self):\n" + cat_code + layout_code + "\n"
    
    new_content = content[:build_ui_start] + new_build_ui + content[next_method_start:]
    
    # Fix import
    if "from components.island_layout import IslandLayout, IslandCategory" not in new_content:
        new_content = new_content.replace("import flet as ft", "import flet as ft\nfrom components.island_layout import IslandLayout, IslandCategory")

    with open(file_path, 'w') as f:
        f.write(new_content)
    print(f"Refactored {file_path}")

for py_file in glob.glob('/Users/asper/Programming/Flutter UI:UX/erp_demo/views/*.py'):
    if "auth.py" in py_file or "dashboard.py" in py_file or "settings.py" in py_file:
        continue
    refactor_view(py_file)
