from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException # HTTPException add kiya
from fastapi.responses import JSONResponse # JSONResponse import kiya

from src.codefixer import fix_content
from src.comment_remover import remove_all_comments
import jsbeautifier

app = FastAPI()

# ✅ CORS (frontend connect ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request body structure
class CodeRequest(BaseModel):
    code: str
    remove_unused: bool = False # Default: False, agar client specify nahi karta
    remove_comments: bool = False 

# ✅ API endpoint
@app.post("/process")
def process_code(req: CodeRequest):
    try:
        # 1. Pehle Original Fixer chalao
        result = fix_content(req.code, req.remove_unused)
        
        # 2. Comments remove karna
        if req.remove_comments:
            result = remove_all_comments(result)
            
        # 3. Semicolons & Formatting (not done)

        return {"fixed_code": result}

    # 🌟 NAYA LOGIC: Errors ko yahan smoothly pakdo
    except ValueError as ve:
        # Agar multiple try/catch wali ValueError aayi, toh usko clean 400 error banakar bhejo
        return JSONResponse(status_code=400, content={"detail": str(ve)})
        
    except Exception as e:
        # Agar koi aur backend crash hota hai, toh bhi CORS na fate
        return JSONResponse(status_code=500, content={"detail": f"Server logic error: {str(e)}"})








# 👉 Optional: local testing (terminal se)
if __name__ == "__main__":
    print(fix_content("var a = 10; testing code."))