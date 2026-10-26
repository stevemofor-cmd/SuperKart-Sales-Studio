# SuperKart Sales Studio

Independent end-to-end regression and deployment submission for estimating
product-store sales from the supplied SuperKart data.

## Run with GitHub Codespaces

Open this repository in a Codespace. The devcontainer builds and starts the
Flask API and Streamlit interface. Open forwarded port **8501** for the
interface; keep API port **7860** private. In the app, use the single-product
form for raw product/store details. For batch inference, upload the supplied
model-ready CSV or download the template from the app.

## Run locally with Docker

From the repository root:

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Open `http://localhost:8501`. The API is available locally at
`http://localhost:7860`.

## Reproduce the notebook

Run `Steve_SuperKart_Full_Code_Submission.ipynb` from the repository root in
the provided Python environment. It documents the data exploration, model
selection, evaluation, serialization, deployment sources, and local inference
checks. The accompanying HTML is the executed notebook export.
