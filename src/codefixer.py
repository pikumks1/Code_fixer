# main code, called in main.py
import os
import re

import jsbeautifier

def fix_content(content):
    # The Regex: 
    # Group 1: Matches // comments
    # Group 2: Matches /* */ comments
    # Group 3: Matches the 'var ... ;' block
    regex_pattern = r"(//.*)|(/\*[\s\S]*?\*/)|(var\s+[^;]+;)"

    found_variables = []

    for match in re.finditer(regex_pattern, content):
        # Only process if we found a 'var' block
        if match.group(3):
            var_block = match.group(3)
            # Clean: Remove 'var' and ';'
            clean_block = re.sub(r"^\s*var\s+", "", var_block).rstrip(';').strip()
            
            # It removes everything inside ( ) so commas in function calls don't cause wrong splits
            clean_block = re.sub(r'\(.*?\)', '', clean_block)

            #print (f"Processing var block: '{clean_block}'")
            
            # Split by comma for cases like: var boAcc, bcAcc;
            parts = clean_block.split(',')
            for p in parts:
                # 1. Get the name before the '=' sign (if initialized)
                name_part = p.split('=')[0].strip()
                
                # 2. FIX: Handle typed variables (qty:Number -> qty)
                name = name_part.split(':')[0].strip()

                # 3. CHANGE HERE: Validate that 'name' is a proper variable identifier
                # This skips "Inp", "TEST_LOV", or anything with quotes/brackets
                if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', name):
                    if name and name not in found_variables:
                        # Append in order of appearance
                        found_variables.append(name)

    # 3. REVERSE the list for Bottom-Up nullification
    all_vars = found_variables[::-1]

    # --- NAYA LOGIC: Usage Check After Finally Block ---
    # Sabse pehle identify karte hain ki function body mein finally kahan khatam ho raha hai
    body_match = re.search(r"(\{)(.*)(\})", content, re.DOTALL)
    if not body_match:
        return content
    
    inner_body = body_match.group(2)
    
    # Search for an existing finally block to see if there is code after it
    existing_finally = re.search(r"finally\s*\{.*?\}", inner_body, re.DOTALL)
    
    if existing_finally:
        # Finally block ke khatam hone ke baad ka code
        post_finally_code = inner_body[existing_finally.end():]
        # Comments hatao taaki false match na ho
        clean_post_code = re.sub(r"(//.*)|(/\*[\s\S]*?\*/)", "", post_finally_code)
        
        filtered_vars = []
        for v in all_vars:
            # Check if variable is used in the remaining code
            if not re.search(rf"\b{re.escape(v)}\b", clean_post_code):
                filtered_vars.append(v)
            else:
                print(f"Skipping {v}: Found usage after finally block.")
        all_vars = filtered_vars
    # --- End of Naya Logic ---

    print(f"Found variables (Bottom-Up order): {all_vars}")

    
    if not all_vars:
        return content
    
    # Generate the nullifying statements for the finally block
    nullify_logic = "".join([f"\n        if(defined({v})) {v} = null;" for v in all_vars])
    
    # Identify the function body (content between the first { and last })
    body_match = re.search(r"(\{)(.*)(\})", content, re.DOTALL)
    if not body_match:
        return content
    
    
    
    # 1. Create a version of the body with ALL comments removed for searching
    # This removes // single-line and /* multi-line */ comments
    clean_body_for_search = re.sub(r"(//.*)|(/\*[\s\S]*?\*/)", "", body_match.group(2))

    #print(f"Clean body for search: {clean_body_for_search}")

    # 2. Use word boundaries (\b) to find and count active keywords
    try_matches = re.findall(r"\btry\b", clean_body_for_search)
    catch_matches = re.findall(r"\bcatch\b", clean_body_for_search)
    finally_matches = re.findall(r"\bfinally\b", clean_body_for_search)

    # 3. Get the counts
    try_count = len(try_matches)
    catch_count = len(catch_matches)
    finally_count = len(finally_matches)

    # 4. Set your flags based on the counts
    has_try = try_count > 0
    has_catch = catch_count > 0
    has_finally = finally_count > 0

    print(f"Blocks found -> Try: {try_count}, Catch: {catch_count}, Finally: {finally_count}")
    
    if try_count > 1 or catch_count > 1 or finally_count > 1:
        # Yeh message aapki website ke frontend par bheja ja sakta hai
        raise ValueError("Multiple try blocks detected! Please fix manually.")
        #breakpoint() -- dubugging k case me lagana h
    

    opening, inner_body, closing = body_match.groups()
    stripped_body = inner_body.strip()

    """# Check for presence of keywords
    has_try = "try" in stripped_body
    has_catch = "catch" in stripped_body
    has_finally = "finally" in stripped_body"""

    # CASE 1: None are there (Wrap everything)
    if not has_try and not has_catch and not has_finally:
        new_content = (
            f"try {{\n        {stripped_body}\n    }} "
            f"catch(e) {{\n        throw e;\n    }} "
            f"finally {{{nullify_logic}\n    }}"
        )
        return content.replace(inner_body, f"\n    {new_content}\n")

    # CASE 2: Only 'try' is there (Add catch and finally)
    if has_try and not has_catch and not has_finally:
        # Append catch and finally after the try block's closing brace
        # This regex looks for the last '}' of the try block
        new_content = re.sub(r"(try\s*\{.*?\})(\s*)(?!catch|finally)", 
                             r"\1 catch(e) {\n        throw e;\n    } finally {" + nullify_logic + "\n    }", 
                             stripped_body, flags=re.DOTALL)
        return content.replace(inner_body, f"\n    {new_content}\n")

    # CASE 3: 'try' and 'catch' are there (Add only finally)
    if has_try and has_catch and not has_finally:
        # Append finally after the catch block
        new_content = re.sub(r"(catch\s*\(.*?\)\s*\{.*?\})(\s*)(?!finally)", 
                             r"\1 finally {" + nullify_logic + "\n    }", 
                             stripped_body, flags=re.DOTALL)
        return content.replace(inner_body, f"\n    {new_content}\n")
    
    # CASE 4: 'try' and 'finally' are there (Add only catch) and add nullification logic in finally
    if has_try and not has_catch and has_finally:
        # Append catch after the try block
        new_content = re.sub(r"(try\s*\{.*?\})(\s*)(?!catch)", 
                             r"\1 catch(e) {\n        throw e;\n    }", 
                             stripped_body, flags=re.DOTALL)
        # Now, we also need to ensure the nullification logic is in the finally block
        finally_match = re.search(r"finally\s*\{([^}]*)\}", new_content, re.DOTALL)
        if finally_match:
            existing_inner = finally_match.group(1)
            if nullify_logic.strip() not in existing_inner:
                new_finally = f"finally {{{existing_inner}{nullify_logic}\n    }}"
                new_content = new_content.replace(finally_match.group(0), new_finally)
        return content.replace(inner_body, f"\n    {new_content}\n")

    # CASE 5: 'try', 'catch', and 'finally' are all present (Append missing variables)
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
input_folder = "./scripts_to_fix"  # Create this folder and put your files inside
output_folder = "./scripts_fixed"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for filename in os.listdir(input_folder):
    if filename.endswith(".js") or filename.endswith(".txt"):
        print(f"Processing: {filename}...")
        with open(os.path.join(input_folder, filename), "r") as f:
            data = f.read()
        
        fixed_data = fix_content(data)
        ##fixed_data = jsbeautifier.beautify(fixed_data)  # Beautify the final output for better readability
        with open(os.path.join(output_folder, filename), "w") as f:
            f.write(fixed_data)

print("\n✅ Done! Check the 'scripts_fixed' folder.")