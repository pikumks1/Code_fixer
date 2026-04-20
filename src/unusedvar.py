import re

# ==========================================
# HELPER: Safe Comma Splitter
# ==========================================
def split_var_declarations(var_content):
    parts = []
    current = []
    paren_level = 0
    brace_level = 0
    for char in var_content:
        if char == '(': paren_level += 1
        elif char == ')': paren_level -= 1
        elif char == '{': brace_level += 1
        elif char == '}': brace_level -= 1
            
        if char == ',' and paren_level <= 0 and brace_level <= 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return parts

# ==========================================
# STEP 2: Filter Ignored Cases (UPDATED FOR FUNCTION CALLS)
# ==========================================
def step_2_filter_ignored_vars(extracted_vars, safe_code):
    vars_to_check = set()
    var_regex = r"(\bvar\s+)([^;]+?)(;)"
    
    # Pehle sab variables ka Right-Hand Side (RHS) nikal lete hain
    var_initializations = {}
    for match in re.finditer(var_regex, safe_code):
        parts = split_var_declarations(match.group(2))
        for p in parts:
            # Name aur uske baad ka sab kuch (assignment) alag karo
            name_match = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)(.*)', p.strip())
            if name_match:
                v_name = name_match.group(1)
                v_rhs = name_match.group(2) # e.g., ' = testfunc(a,b)'
                
                if v_name not in var_initializations:
                    var_initializations[v_name] = []
                var_initializations[v_name].append(v_rhs)

    for var in extracted_vars:
        should_ignore = False
        
        # Rule 1 & 2: Check its initializations
        if var in var_initializations:
            for rhs in var_initializations[var]:
                # RULE: Agar variable kisi function call, mathematical expression '()' 
                # ya 'function' keyword se assign hua hai, toh usko Bacha lo!
                if '(' in rhs or 'function' in rhs:
                    should_ignore = True
                    print(f"🛡️ Protected (Function Call/Def): {var}")
                    break
        
        if not should_ignore:
            vars_to_check.add(var)
            
    return vars_to_check

# ==========================================
# STEP 3: Identify Truly Unused Variables (Updated for "" and Spaces)
# ==========================================
def step_3_find_unused(vars_to_check, safe_code):
    unused_vars = set()
    var_regex = r"(\bvar\s+)([^;]+?)(;)"
    
    for var in vars_to_check:
        test_code = safe_code
        escaped_var = re.escape(var)
        
        # Pattern for null or empty string: (null|"")
        # \s* handles any number of spaces or tabs
        null_or_empty = r'(?:null|"")'
        
        # 1. Erase: if(defined(x)) { x = "" } or x = null
        p1 = rf'if\s*\(\s*defined\s*\(\s*\b{escaped_var}\b\s*\)\s*\)\s*\{{?\s*\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?\s*\}}?'
        test_code = re.sub(p1, '', test_code)
        
        # 2. Erase: if(x != null) or if(x != "")
        p2 = rf'if\s*\(\s*\b{escaped_var}\b\s*!=\s*{null_or_empty}\s*\)\s*\{{?\s*\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?\s*\}}?'
        test_code = re.sub(p2, '', test_code)
        
        # 3. Erase: Direct assignment with any spaces -> x    =    ""
        p3 = rf'\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?'
        test_code = re.sub(p3, '', test_code)
        
        # Count checking
        remaining_occurrences = len(re.findall(rf'\b{escaped_var}\b', test_code))
        
        decl_count = 0
        for match in re.finditer(var_regex, test_code):
            parts = split_var_declarations(match.group(2))
            for p in parts:
                name_match = re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)', p.strip())
                if name_match and name_match.group(1) == var:
                    decl_count += 1
                    
        if remaining_occurrences == decl_count:
            unused_vars.add(var)
            
    return unused_vars

# ==========================================
# STEP 4: Remove Unused Variables
# ==========================================
def step_4_remove_from_code(safe_code, unused_vars):
    var_regex = r"(\bvar\s+)([^;]+?)(;)"
    null_or_empty = r'(?:null|"")'
    
    for var in unused_vars:
        escaped_var = re.escape(var)
        
        # Aggressively remove all clearing patterns from the actual code
        p1 = rf'if\s*\(\s*defined\s*\(\s*\b{escaped_var}\b\s*\)\s*\)\s*\{{?\s*\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?\s*\}}?'
        safe_code = re.sub(p1, '', safe_code)
        
        p2 = rf'if\s*\(\s*\b{escaped_var}\b\s*!=\s*{null_or_empty}\s*\)\s*\{{?\s*\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?\s*\}}?'
        safe_code = re.sub(p2, '', safe_code)
        
        p3 = rf'\b{escaped_var}\b\s*=\s*{null_or_empty}\s*;?'
        safe_code = re.sub(p3, '', safe_code)

    # Clean the declaration line
    def clean_var_statement(match):
        prefix, var_block, suffix = match.group(1), match.group(2), match.group(3)
        parts = split_var_declarations(var_block)
        kept_parts = [p for p in parts if not (re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)', p.strip()) and re.match(r'^([a-zA-Z_$][a-zA-Z0-9_$]*)', p.strip()).group(1) in unused_vars)]
        
        if not kept_parts: return ""
        return prefix + ", ".join(kept_parts) + suffix

    safe_code = re.sub(var_regex, clean_var_statement, safe_code)
    return safe_code

# ==========================================
# MAIN ORCHESTRATOR (With Crash Handler)
# ==========================================
def clean_modular_code(content, extracted_vars):
    try:
        protected_items = []
        def save_item(match):
            protected_items.append(match.group(0))
            return f"__PROTECTED_{len(protected_items)-1}__"

        protection_pattern = r"(//.*)|(/\*[\s\S]*?\*/)|(\"(?:\\.|[^\"\\])*\")|(\'(?:\\.|[^\'\\])*\')"
        safe_code = re.sub(protection_pattern, save_item, content)

        vars_to_check = step_2_filter_ignored_vars(extracted_vars, safe_code)
        unused_vars = step_3_find_unused(vars_to_check, safe_code)
        
        if unused_vars:
            print(f"🧹 Removing unused: {unused_vars}")
            safe_code = step_4_remove_from_code(safe_code, unused_vars)
            
        def restore_item(match):
            return protected_items[int(match.group(1))]
            
        final_code = re.sub(r"__PROTECTED_(\d+)__", restore_item, safe_code)
        final_code = re.sub(r'\n\s*\n', '\n', final_code)
        
        remaining_vars = [v for v in extracted_vars if v not in unused_vars]
        
        return final_code, remaining_vars

    except Exception as e:
        # 🚨 AGAR CODE FATEGA, TOH YAHAN PAKDA JAYEGA!
        print("\n" + "="*40)
        print("🚨 PYTHON CRASH REPORT 🚨")
        print(f"Error Message: {e}")
        import traceback
        traceback.print_exc()  # Ye exact line number batayega
        print("="*40 + "\n")
        
        # Original code wapas bhej do taaki UI par loader atakne ki bimari khatam ho
        return content, extracted_vars