from fastapi import FastAPI, UploadFile, File, Response

app = FastAPI()

@app.post("/process")
async def process(file: UploadFile = File(...)):
    # run your redaction, produce bytes_out and a flag
    bytes_out, applied = await redact_image(await file.read())
    headers = {"x-redactions": "some" if applied else "none"}
    return Response(content=bytes_out, media_type="application/octet-stream", headers=headers)
