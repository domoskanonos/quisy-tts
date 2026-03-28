from fastapi import APIRouter, HTTPException, Request
from api.dependencies import get_tts_service
from schemas import TTSParams
import os
from config import ProjectConfig

router = APIRouter()
settings = ProjectConfig.get_settings()


@router.post("/generate/ssml")
async def generate_ssml(request: Request):
    ssml_content = await request.body()
    tts_service = get_tts_service()

    try:
        # Base parameters for the generation
        base_params = TTSParams(mode="custom_voice", model_size="1.7B")

        result_path = await tts_service.generate_from_ssml(ssml_content.decode("utf-8"), base_params)

        # Return URL
        filename = os.path.basename(result_path)
        return {"url": f"http://localhost:{settings.PORT}/audio/{filename}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
