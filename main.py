from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
    # 1. Pehle Original Fixer chalao
    result = fix_content(req.code, req.remove_unused)
    
    # 2. Agar user ne Comments remove karne ko bola hai
    if req.remove_comments:
        result = remove_all_comments(result)
        

    return {"fixed_code": result}


# 👉 Optional: local testing (terminal se)
if __name__ == "__main__":
    print(fix_content("var a = 10; testing code."))