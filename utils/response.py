from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
def success_response(
        data,
        message: str = "Success"
):
    content = {
        "data": data,
        "message": message,
        "code": 200
    }
    return JSONResponse(content=jsonable_encoder(content))