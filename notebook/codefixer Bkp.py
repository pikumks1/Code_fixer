# main code, called in main.py
import os
import re

def fix_content(content):
    # The Regex: 
    # Group 1: Matches // comments
    # Group 2: Matches /* */ comments
    # Group 3: Matches the 'var ... ;' block
    regex_pattern = r"(//.*)|(/\*[\s\S]*?\*/)|(var\s+[^;]+;)"

    # We will store variables in a dictionary to track their "type" for sorting
    # Priority 1: BC (GetBusComp), Priority 2: BO (GetBusObject), Priority 3: Others
    var_priority_map = {}
    for match in re.finditer(regex_pattern, content):
        if match.group(3):
            var_block = match.group(3)
            clean_block = var_block.replace("var", "").replace(";", "").strip()
            
            # Split by comma for cases like: var boAcc = ..., bcAcc = ...;
            parts = clean_block.split(',')
            for p in parts:
                if '=' in p:
                    name_part, value_part = p.split('=', 1)
                    name = name_part.strip()
                    value = value_part.strip()

                    # Logic for Case 1 & 2
                    if "GetBusComp" in value:
                        priority = 1  # BC gets highest priority for nullification
                    elif "GetBusObject" in value:
                        priority = 2  # BO comes after BC
                    else:
                        priority = 3  # Standard variables
                else:
                    # Case where variable is declared but not assigned here
                    name = p.strip()
                    priority = 3 

                if name:
                    # If variable appears multiple times, we keep the most "critical" priority
                    if name not in var_priority_map or priority < var_priority_map[name]:
                        var_priority_map[name] = priority

    # Sort the variable names based on the assigned priority
    # This ensures BC (1) comes before BO (2)
    all_vars = sorted(var_priority_map.keys(), key=lambda x: var_priority_map[x])

    ##print(f"Found variables to nullify (Sorted BC -> BO): {all_vars}")
    
    if not all_vars:
        return content
    
    # Generate the nullifying statements for the finally block
    nullify_logic = "".join([f"\n        if(defined({v})) {v} = null;" for v in all_vars])
    
    # Identify the function body (content between the first { and last })
    body_match = re.search(r"(\{)(.*)(\})", content, re.DOTALL)
    if not body_match:
        return content
    
    opening, inner_body, closing = body_match.groups()
    stripped_body = inner_body.strip()

    # Check for presence of keywords
    has_try = "try" in stripped_body
    has_catch = "catch" in stripped_body
    has_finally = "finally" in stripped_body

    # CASE 3: None are there (Wrap everything)
    if not has_try and not has_catch and not has_finally:
        new_content = (
            f"try {{\n        {stripped_body}\n    }} "
            f"catch(e) {{\n        throw e;\n    }} "
            f"finally {{{nullify_logic}\n    }}"
        )
        return content.replace(inner_body, f"\n    {new_content}\n")

    # CASE 1: Only 'try' is there (Add catch and finally)
    if has_try and not has_catch and not has_finally:
        # Append catch and finally after the try block's closing brace
        # This regex looks for the last '}' of the try block
        new_content = re.sub(r"(try\s*\{.*?\})(\s*)(?!catch|finally)", 
                             r"\1 catch(e) {\n        throw e;\n    } finally {" + nullify_logic + "\n    }", 
                             stripped_body, flags=re.DOTALL)
        return content.replace(inner_body, f"\n    {new_content}\n")

    # CASE 2: 'try' and 'catch' are there (Add only finally)
    if has_try and has_catch and not has_finally:
        # Append finally after the catch block
        new_content = re.sub(r"(catch\s*\(.*?\)\s*\{.*?\})(\s*)(?!finally)", 
                             r"\1 finally {" + nullify_logic + "\n    }", 
                             stripped_body, flags=re.DOTALL)
        return content.replace(inner_body, f"\n    {new_content}\n")
    
    # CASE 4: try, catch, and finally are all present (Append missing variables)
    if has_try and has_catch and has_finally:
        finally_match = re.search(r"finally\s*\{([^}]*)\}", stripped_body, re.DOTALL)
        if finally_match:
            existing_inner = finally_match.group(1)
            
            # Filter variables: only add if the exact variable name is NOT found in the block
            to_add = []
            for v in all_vars:
                # \b matches the position at the start or end of a word
                # re.escape handles variables with special characters if any
                if not re.search(rf"\b{re.escape(v)}\b", existing_inner):
                    to_add.append(f"\n        if(defined({v})) {v} = null;")

            if to_add:
                # Append the new nullification statements before the closing brace
                new_finally = f"finally {{{existing_inner}{''.join(to_add)}\n    }}"
                new_content = stripped_body.replace(finally_match.group(0), new_finally)
                return content.replace(inner_body, f"\n    {new_content}\n")

    return content


# --- Main Logic to Loop Through Folder ---
input_folder = "./data/scripts_to_fix"  # Create this folder and put your files inside
output_folder = "./data/scripts_fixed"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for filename in os.listdir(input_folder):
    if filename.endswith(".js") or filename.endswith(".txt"):
        print(f"Processing: {filename}...")
        with open(os.path.join(input_folder, filename), "r") as f:
            data = f.read()
        
        fixed_data = fix_content(data)
        
        with open(os.path.join(output_folder, filename), "w") as f:
            f.write(fixed_data)

print("\n✅ Done! Check the 'scripts_fixed' folder.")