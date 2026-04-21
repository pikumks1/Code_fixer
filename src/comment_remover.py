import re

def remove_all_comments(code):
    print("🧹 Removing Comments...")
    
    # STEP 1: Protect Strings (taaki "http://..." jaisi strings kharab na hon)
    protected_strings = []
    def save_string(match):
        protected_strings.append(match.group(0))
        return f"__STR_{len(protected_strings)-1}__"

    # Match only "strings" or 'strings'
    string_pattern = r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')'
    safe_code = re.sub(string_pattern, save_string, code)

    # STEP 2: Remove Comments (Single line // and Multi-line /* */)
    comment_pattern = r'(//.*)|(/\*[\s\S]*?\*/)'
    safe_code = re.sub(comment_pattern, '', safe_code)

    # STEP 3: Restore Strings
    def restore_string(match):
        idx = int(match.group(1))
        return protected_strings[idx]

    final_code = re.sub(r'__STR_(\d+)__', restore_string, safe_code)

    # STEP 4: Remove extra blank lines left by deleted comments
    final_code = re.sub(r'\n\s*\n', '\n', final_code)
    
    return final_code