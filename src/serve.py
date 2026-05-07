from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import joblib
import os

app = FastAPI()


def _bucket_name() -> str:
    """Ten bucket AWS: bien S3_BUCKET hoac CLOUD_BUCKET (trung voi secret GitHub)."""
    bucket = os.environ.get("S3_BUCKET") or os.environ.get("CLOUD_BUCKET")
    if not bucket:
        raise RuntimeError("Missing env S3_BUCKET or CLOUD_BUCKET")
    return bucket


S3_MODEL_KEY = "models/latest/model.pkl"
MODEL_PATH = os.path.expanduser("~/models/model.pkl")

LABEL_MAP = {
    0: "thap",
    1: "trung_binh",
    2: "cao",
}


def download_model() -> None:
    """Tai file model.pkl tu S3 ve may luc server khoi dong."""
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    bucket = _bucket_name()
    region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")
    kwargs = {} if not region else {"region_name": region}
    boto3.client("s3", **kwargs).download_file(bucket, S3_MODEL_KEY, MODEL_PATH)
    print(f"Da tai model tu s3://{bucket}/{S3_MODEL_KEY}")


download_model()
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    features: list[float]


@app.get("/health")
def health():
    """Health check cho GitHub Actions sau deploy."""
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    """
    Dau vao: JSON {"features": [f1, f2, ..., f12]}
    Dau ra:  JSON {"prediction": <0|1|2>, "label": ...}
    """
    if len(req.features) != 12:
        raise HTTPException(status_code=400, detail="Expected 12 features (wine quality)")
    preds = model.predict([req.features])
    pred = int(preds[0])
    label = LABEL_MAP[pred]
    return {"prediction": pred, "label": label}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
