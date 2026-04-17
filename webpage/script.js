let diffEditor;

// Initialize Global Tracker for Snippet Insertion
window.lastFocusedEditor = 'original';

// Initialize Monaco Editor
require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@latest/min/vs' }});

require(['vs/editor/editor.main'], function () {

    diffEditor = monaco.editor.createDiffEditor(
        document.getElementById('diffEditor'),
        {
            theme: "vs",
            automaticLayout: true,
            renderSideBySide: true, // Locks 2 windows side-by-side
            enableSplitViewResizing: false // Keeps the middle divider fixed
        }
    );

    const originalModel = monaco.editor.createModel("// Paste your original Siebel eScript here", "javascript");
    const modifiedModel = monaco.editor.createModel("// Optimized code will appear here", "javascript");

    diffEditor.setModel({
        original: originalModel,
        modified: modifiedModel
    });

    const originalEditor = diffEditor.getOriginalEditor();
    const modifiedEditor = diffEditor.getModifiedEditor();

    originalEditor.updateOptions({ readOnly: false });
    modifiedEditor.updateOptions({ readOnly: false });

    // --- TRACKERS: Remember the last clicked editor ---
    originalEditor.onDidFocusEditorWidget(() => {
        window.lastFocusedEditor = 'original';
    });

    modifiedEditor.onDidFocusEditorWidget(() => {
        window.lastFocusedEditor = 'modified';
    });

    // Page load hote hi dropdown generate karo
    loadSnippets();
});

// Theme configuration
let isDark = false; // Default is light theme ("vs")

function toggleTheme() {
    isDark = !isDark;
    const theme = isDark ? "vs-dark" : "vs";
    monaco.editor.setTheme(theme);
}

// Core API interaction and UI state management
async function processCode() {
    const originalCode = diffEditor.getModel().original.getValue();
    const loader = document.getElementById("loaderOverlay");

    // Display the loading indicator during the API call
    loader.style.display = "flex";

    try {
        const res = await fetch("https://code-fixer-568v.onrender.com/process", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code: originalCode })
        });

        if (!res.ok) {
            throw new Error(`Server responded with status: ${res.status}`);
        }

        const data = await res.json();
        
        // Populate the modified editor with the optimized code
        diffEditor.getModel().modified.setValue(data.fixed_code);

    } catch (error) {
        console.error("API Connection Failed:", error);
        alert("Unable to connect to the optimization server. Please check your network connection or review the console logs for details.");
    } finally {
        // Ensure the loading overlay is dismissed regardless of the outcome
        loader.style.display = "none";
    }
}

// Code formatting utility utilizing Monaco's built-in actions
async function beautifyCode1() {
    const editor = diffEditor.getModifiedEditor();
    editor.focus();
    await editor.getAction('editor.action.formatDocument').run();
}

// New beautify function with user-configurable options and ASI logic
// Toggle the Settings Modal
function toggleBeautifySettings() {
    const modal = document.getElementById("beautifyModal");
    modal.style.display = modal.style.display === "none" ? "flex" : "none";
}

// Basic Auto-Semicolon (ASI) logic for common Siebel/JS lines
function autoInsertSemicolons(code) {
    // Ye regex simple variables, returns aur function calls ke aage semicolon lagata hai agar miss ho
    // Reality Check: Ye 100% perfect nahi hota, isliye Beta likha hai.
    return code.replace(/(^[\t ]*(?:var|let|const|return|TheApplication|bc|bo)[^;{\n]+)(?=\n|$)/gm, "$1;");
}

// Advanced Formatter using User Settings
function beautifyCode() {
    const originalEditor = diffEditor.getOriginalEditor();
    const modifiedEditor = diffEditor.getModifiedEditor();
    
    let origCode = originalEditor.getValue();
    let modCode = modifiedEditor.getValue();

    // 1. Fetch values from our Settings Modal
    const indentVal = document.getElementById("opt_indent").value;
    const braceVal = document.getElementById("opt_braces").value;
    const lineVal = parseInt(document.getElementById("opt_lines").value);
    const doSemicolon = document.getElementById("opt_semicolon").checked;

    // Optional: Pre-process for missing semicolons
    if (doSemicolon) {
        //if (origCode && !origCode.includes("Paste your original")) origCode = autoInsertSemicolons(origCode);
        if (modCode && !modCode.includes("Optimized code will")) modCode = autoInsertSemicolons(modCode);
    }

    // 2. Setup js-beautify exactly like beautifier.io
    const formatOptions = {
        indent_size: indentVal === "tab" ? 4 : parseInt(indentVal),
        indent_char: indentVal === "tab" ? "\t" : " ",
        indent_with_tabs: indentVal === "tab",
        brace_style: braceVal,
        max_preserve_newlines: lineVal,
        preserve_newlines: lineVal > 0,
        space_before_conditional: true,
        jslint_happy: true, // Function ke aage space
        end_with_newline: true
    };

    // 3. Apply the magic
    //if (origCode && !origCode.includes("Paste your original")) {
   //     originalEditor.setValue(js_beautify(origCode, formatOptions));
   // }
    
    if (modCode && !modCode.includes("Optimized code will")) {
        modifiedEditor.setValue(js_beautify(modCode, formatOptions));
    }
}

// Clears the editors and resets them to their default placeholder states
function clearCode() {
    // Resetting content to base state
    diffEditor.getModel().original.setValue("// Paste your original Siebel eScript here\n");
    diffEditor.getModel().modified.setValue("// Optimized code will appear here\n");
    
    // Reset internal focus tracker
    window.lastFocusedEditor = 'original';
}

// Utility to securely copy the optimized code to the user's clipboard
async function copyFixedCode() {
    try {
        const fixedCode = diffEditor.getModel().modified.getValue();
        
        // Prevent copying empty or placeholder text
        if (!fixedCode || fixedCode.includes("Optimized code will appear here")) {
            alert("Please fix the code first before copying.");
            return;
        }
        
        await navigator.clipboard.writeText(fixedCode);
        alert("Code copied to clipboard!");
    } catch (error) {
        console.error("Clipboard copy operation failed:", error);
        alert("Failed to copy code. Please check your browser's clipboard permissions.");
    }
}

// Utility to generate and download a clean .js file for Siebel import
function downloadFixedCode() {
    const fixedCode = diffEditor.getModel().modified.getValue();
    
    // Prevent downloading empty or placeholder text
    if (!fixedCode || fixedCode.includes("Optimized code will appear here")) {
        alert("Please fix the code first before downloading.");
        return;
    }

    // Create a Blob object representing the data as a JavaScript file
    const blob = new Blob([fixedCode], { type: "text/javascript" });
    const url = window.URL.createObjectURL(blob);
    
    // Create a temporary anchor tag to trigger the download
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "optimized_siebel_script.js";
    
    document.body.appendChild(anchor);
    anchor.click();
    
    // Clean up the DOM and release memory
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
}

// Siebel Standard Boilerplates for quick insertion snippets
// --- 1. Standard Default Snippets (Read-Only) ---
const defaultSnippets = {
    "Error Handling": 
`var bs = TheApplication().GetService("Error Handling Service");
var bsInputs = TheApplication().NewPropertySet();
var bsOutputs = TheApplication().NewPropertySet();
bsInputs.SetProperty("ErrorMessage", e.message);
bsInputs.SetProperty("ErrorCode", e.Code);
bsInputs.SetProperty("ErrorObjectId", "ROW_ID");
bs.InvokeMethod("LogError", bsInputs, bsOutputs);`,

    "Query (ForwardOnly)": 
`var bo = TheApplication().GetBusObject("Your_BO_Name");
var bc = bo.GetBusComp("Your_BC_Name");
try {
    bc.ClearToQuery();
    bc.SetSearchExpr("[Name] = 'Enter_Value'");
    bc.ExecuteQuery(ForwardOnly);
    
    if (bc.FirstRecord()) {
        // Add your logic here
    }
} catch (e) {
    throw e;
} finally {
    if (defined(bc)) bc = null;
    if (defined(bo)) bo = null;
}`,

    "Standard BS Method": 
`function Service_PreInvokeMethod (MethodName, Inputs, Outputs) {
    try {
        if (MethodName === "YourMethodName") {
            return (CancelOperation);
        }
        return (ContinueOperation);
    } catch (e) {
        throw e;
    } finally {
    }
}`
};

// Global variable to hold all snippets currently loaded
let allActiveSnippets = {};

// --- 2. Initialize and Load Snippets from LocalStorage ---
function loadSnippets() {
    const selector = document.getElementById("snippetSelector");
    selector.innerHTML = '<option value="" disabled selected>⚡ Insert Snippet...</option>';

    // Fetch custom snippets from browser's local storage
    const storedSnippets = localStorage.getItem('customSiebelSnippets');
    const customSnippets = storedSnippets ? JSON.parse(storedSnippets) : {};

    // Combine defaults and customs
    allActiveSnippets = { ...defaultSnippets, ...customSnippets };

    // Group 1: Add Default Snippets to Dropdown
    const optGroupDefault = document.createElement('optgroup');
    optGroupDefault.label = "Standard Boilerplates";
    for (const key in defaultSnippets) {
        optGroupDefault.innerHTML += `<option value="${key}">${key}</option>`;
    }
    selector.appendChild(optGroupDefault);

    // Group 2: Add Custom Snippets to Dropdown (if any exist)
    if (Object.keys(customSnippets).length > 0) {
        const optGroupCustom = document.createElement('optgroup');
        optGroupCustom.label = "My Custom Snippets";
        for (const key in customSnippets) {
            optGroupCustom.innerHTML += `<option value="${key}">${key} (Local)</option>`;
        }
        selector.appendChild(optGroupCustom);
    }
}

// --- 3. Save Custom Snippet Logic ---
function saveCustomSnippet() {
    // Get active editor based on tracker
    const activeEditor = window.lastFocusedEditor === 'modified' ? diffEditor.getModifiedEditor() : diffEditor.getOriginalEditor();
    
    // Check if user has selected specific text, otherwise take the whole file
    const selection = activeEditor.getSelection();
    let textToSave = activeEditor.getModel().getValueInRange(selection);
    
    if (!textToSave.trim()) {
        textToSave = activeEditor.getValue();
    }

    // Validation
    if (!textToSave.trim() || textToSave.includes("Paste your original Siebel eScript here")) {
        alert("Please write or highlight some valid code in the editor to save as a snippet.");
        return;
    }

    const snippetName = prompt("Enter a name for your custom snippet:\n(e.g., My Workflow Caller)");
    if (!snippetName || !snippetName.trim()) return;

    // Fetch existing from storage, append new, and save back
    const storedSnippets = localStorage.getItem('customSiebelSnippets');
    const customSnippets = storedSnippets ? JSON.parse(storedSnippets) : {};
    
    customSnippets[snippetName.trim()] = textToSave;
    localStorage.setItem('customSiebelSnippets', JSON.stringify(customSnippets));

    // Reload the dropdown to show the new snippet
    loadSnippets();
    alert(`Snippet "${snippetName}" saved successfully to your browser!`);
}

// --- 4. Updated Insert Snippet Logic ---
function insertSnippet() {
    const selector = document.getElementById("snippetSelector");
    const snippetKey = selector.value;
    
    if (!snippetKey || !allActiveSnippets[snippetKey]) return;

    const originalEditor = diffEditor.getOriginalEditor();
    const modifiedEditor = diffEditor.getModifiedEditor();
    const activeEditor = window.lastFocusedEditor === 'modified' ? modifiedEditor : originalEditor;
    
    let position = activeEditor.getPosition();
    if (!position) position = { lineNumber: 1, column: 1 };
    
    activeEditor.executeEdits("snippetInsert", [{
        range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
        text: allActiveSnippets[snippetKey],
        forceMoveMarkers: true
    }]);

    selector.selectedIndex = 0; 
    
    activeEditor.focus();
    setTimeout(() => { activeEditor.getAction('editor.action.formatDocument').run(); }, 50);
}

// --- File Upload Logic ---
function handleFileUpload(event) {
    const file = event.target.files[0];
    
    // Agar user ne popup open karke cancel kar diya
    if (!file) return;

    // Validation: Sirf JS ya Text file allow karenge
    if (!file.name.endsWith('.js') && !file.name.endsWith('.txt')) {
        alert("Please upload .js or .txt file.!");
        event.target.value = ''; // Reset input
        return;
    }

    const reader = new FileReader();
    
    // Jab file poori read ho jaye
    reader.onload = function(e) {
        const fileContent = e.target.result;
        
        // 1. Left (Original) editor me file ka code daalo
        diffEditor.getModel().original.setValue(fileContent);
        
        // 2. Right (Modified) editor ko reset kar do taaki purana code na dikhe
        diffEditor.getModel().modified.setValue("// Uploaded file loaded. Click Process to optimize.\n");
        
        // 3. Focus reset kar do
        window.lastFocusedEditor = 'original';
    };

    // File ko as a Text read karna shuru karo
    reader.readAsText(file);
    
    // Input ko clear kar do taaki same file dobara select ho sake
    event.target.value = '';
}