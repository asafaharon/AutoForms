from pydantic import BaseModel

class GenerateResp(BaseModel):
    form_id: str
    html: str
    embed: str
