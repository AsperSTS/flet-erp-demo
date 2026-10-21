import glob

for py_file in glob.glob('/Users/asper/Programming/Flutter UI:UX/erp_demo/views/*.py'):
    with open(py_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    in_bad_block = False
    modified = False
    
    for line in lines:
        if line.startswith("        def build_ui(self):"):
            new_lines.append("    def build_ui(self):\n")
            modified = True
        elif line.startswith("        categories = [") and modified:
            new_lines.append(line) # keep it at 8 spaces (which is correct relative to 4 spaces def)
        else:
            new_lines.append(line)
            
    if modified:
        with open(py_file, 'w') as f:
            f.writelines(new_lines)
        print(f"Fixed {py_file}")
