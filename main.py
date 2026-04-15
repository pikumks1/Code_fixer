from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from src.codefixer import fix_content
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

# ✅ API endpoint
@app.post("/process")
def process_code(req: CodeRequest):
    #print(req.code) -- to debug input
    result = fix_content(req.code)
    ##result = jsbeautifier.beautify(result)
    return {"fixed_code": result}


# 👉 Optional: local testing (terminal se)
if __name__ == "__main__":
    print(fix_content("var a = 10; testing code."))