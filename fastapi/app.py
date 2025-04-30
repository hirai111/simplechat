
m fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import nest_asyncio
import os
from pyngrok import ngrok
import uvicorn
import torch
from transformers import pipeline

# 本番用モデルをデフォルトに設定
MODEL_NAME = "google/gemma-2-2b-jpn-it"

app = FastAPI(title="Simple Chat LLM API")
app.add_middleware(
            CORSMiddleware,
                allow_origins=["*"],
                    allow_methods=["*"],
                        allow_headers=["*"]
                        )

class GenerationRequest(BaseModel):
        prompt: str
            max_new_tokens: int = 128
                temperature: float = 0.7
                    top_p: float = 0.9

                    class GenerationResponse(BaseModel):
                            generated_text: str

                            @app.on_event("startup")
                            async def load_model():
                                    global llm
                                        device = 0 if torch.cuda.is_available() else -1
                                            # use_auth_token=True で gated モデルにアクセス
                                                llm = pipeline(
                                                                "text-generation",
                                                                        model=MODEL_NAME,
                                                                                device=device,
                                                                                        use_auth_token=True
                                                                                            )
                                                    print(f"Loaded model '{MODEL_NAME}' on device={device}")

                                                    @app.post("/generate", response_model=GenerationResponse)
                                                    async def generate(req: GenerationRequest):
                                                            try:
                                                                        out = llm(
                                                                                            req.prompt,
                                                                                                        max_new_tokens=req.max_new_tokens,
                                                                                                                    temperature=req.temperature,
                                                                                                                                top_p=req.top_p
                                                                                                                                        )
                                                                                text = out[0]["generated_text"]
                                                                                        # プロンプトを取り除く
                                                                                                if text.startswith(req.prompt):
                                                                                                                text = text[len(req.prompt):].strip()
                                                                                                                        return GenerationResponse(generated_text=text)
                                                                                                                        except Exception as e:
                                                                                                                                    raise HTTPException(status_code=500, detail=str(e))

                                                                                                                                @app.get("/health")
                                                                                                                                async def health():
                                                                                                                                        return {"status":"ok","model":MODEL_NAME}

                                                                                                                                    def start():
                                                                                                                                            nest_asyncio.apply()
                                                                                                                                                # ngrok トークンを環境変数から取得
                                                                                                                                                    ngrok.set_auth_token(os.environ.get("NGROK_TOKEN", ""))
                                                                                                                                                        url = ngrok.connect(8000).public_url
                                                                                                                                                            print("🚀 Public URL:", url)
                                                                                                                                                                uvicorn.run(app, host="0.0.0.0", port=8000)

                                                                                                                                                                if __name__ == "__main__":
                                                                                                                                                                        start()
                                                                                                                                                                        
