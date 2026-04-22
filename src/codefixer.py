# main code, called in main.py
import os
import re

from src.unusedvar import clean_modular_code
import jsbeautifier

def extract_continue_operation(body_text):
    """
    Sirf aakhiri 'return(ContinueOperation);' ko code se alag karta hai.
    Return karega: (Code_Without_Return, Extracted_Return_String)
    """
    # Regex STRICTLY sirf ContinueOperation ke liye hai. CancelOperation ignore hoga.
    pattern = r"(return\s*\(?\s*ContinueOperation\s*\)?\s*;?(?:\s|//.*|/\*[\s\S]*?\*/)*)$"
    
    match = re.search(pattern, body_text)
    if match:
        extracted = match.group(1).strip()
        # Code body mein se is return line ko kaat lo
        cleaned_body = body_text[:-len(match.group(1))].strip()
        print(f"🛡️ Protected Final Return: {extracted}")
        return cleaned_body, extracted
        
    # Agar nahi mila, toh jaisa tha waisa wapas bhej do
    return body_text, ""


def fix_content(content, remove_unused=False):
    
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
        raise ValueError("Multiple try/catch/finally blocks detected! Please fix manually.")
        #breakpoint() -- dubugging k case me lagana h

        # NAYI LINE:
        #from fastapi import HTTPException
        #raise HTTPException(status_code=400, detail="Multiple try/catch/finally blocks detected! Please fix manually.")
    
    
    
    
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

    # ==========================================
    # 🌟 MODULAR CLEANUP INTEGRATION
    # ==========================================
    if remove_unused:
        # Humne existing code aur array dono pass kiye
        # Ye badle mein saaf kiya hua code aur bache hue zaroori variables wapas dega
        content, all_vars = clean_modular_code(content, all_vars)


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
        raise ValueError("No variables found to nullify in this code!")
        #return content
    
    # Generate the nullifying statements for the finally block
    nullify_logic = "".join([f"\n        if(defined({v})) {v} = null;" for v in all_vars])
    
 ## removed code and moved to top.

    opening, inner_body, closing = body_match.groups()
    stripped_body = inner_body.strip()

    """# Check for presence of keywords
    has_try = "try" in stripped_body
    has_catch = "catch" in stripped_body
    has_finally = "finally" in stripped_body"""

    stripped_body, extracted_return = extract_continue_operation(stripped_body)


    # 🌟 YAHAN BANA HAI HELPER FUNCTION (finalize_content)
    # Iska kaam hai naye code ke aakhiri mein extracted return ko wapas lagana
    def finalize_content(new_body_content):
        if extracted_return:
            new_body_content += f"\n\n        {extracted_return}"
        return content.replace(inner_body, f"\n    {new_body_content}\n")
    # ==============================================================

    # CASE 1: None are there (Wrap everything)
    if not has_try and not has_catch and not has_finally:
        new_content = (
            f"try {{\n    {stripped_body}\n    }} "
            f"catch(e) {{\n        throw e;\n    }} "
            f"finally {{{nullify_logic}\n    }}"
        )
        #return content.replace(inner_body, f"\n    {new_content}\n")
        return finalize_content(new_content)
    
    # CASE 2: Only 'try' is there (Add catch and finally)
    if has_try and not has_catch and not has_finally:
        # Step 1: Find where 'try {' starts
        try_match = re.search(r"\btry\s*\{", stripped_body)
        
        if try_match:
            start_idx = try_match.end() - 1 # '{' ka index
            bracket_count = 0
            insert_pos = -1
            
            # Step 2: Bracket gin kar asli aakhiri '}' dhoondho (nested brackets ignore ho jayenge)
            for i in range(start_idx, len(stripped_body)):
                if stripped_body[i] == '{': 
                    bracket_count += 1
                elif stripped_body[i] == '}': 
                    bracket_count -= 1
                
                # Jab count wapas 0 ho jaye, matlab try block officially khatam
                if bracket_count == 0:
                    insert_pos = i + 1 # '}' ke theek baad wali jagah
                    break
            
            if insert_pos != -1:
                # Step 3: Exact sahi jagah par catch aur finally chipkao
                append_str = f" catch(e) {{\n    throw e;\n    }} finally {{{nullify_logic}\n    }}"
                new_content = stripped_body[:insert_pos] + append_str + stripped_body[insert_pos:]
                return finalize_content(new_content)

        # Agar kisi wajah se loop fail ho jaye (Fallback)
        return finalize_content(stripped_body)

    # CASE 3: 'try' and 'catch' are there (Add only finally)
    if has_try and has_catch and not has_finally:
        # Append finally after the catch block
        new_content = re.sub(r"(catch\s*\(.*?\)\s*\{.*?\})(\s*)(?!finally)", 
                             r"\1 finally {" + nullify_logic + "\n    }", 
                             stripped_body, flags=re.DOTALL)
        #return content.replace(inner_body, f"\n    {new_content}\n")
        return finalize_content(new_content)

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
        #return content.replace(inner_body, f"\n    {new_content}\n")
        return finalize_content(new_content)

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
                return finalize_content(new_content) # <-- YAHAN CALL HUA FINALIZE -- to fix return contine operation issue
                ##return content.replace(inner_body, f"\n    {new_content}\n") 

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