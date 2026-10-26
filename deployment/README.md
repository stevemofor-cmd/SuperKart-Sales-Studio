# SuperKart prediction deployment

The notebook trains, evaluates, serializes, reloads, and smoke-tests the model
before deployment. The saved pipeline is written to
`deployment/backend_files/superkart_model.joblib`; the backend Docker image
intentionally fails to build if that artifact is missing.

## Local execution

From the `prediction_submission` directory:

```bash
python3 -m pip install -r deployment/backend_files/requirements.txt
python3 -m pip install -r deployment/frontend_files/requirements.txt
python3 deployment/backend_files/app.py
```

In a second terminal, start the interface:

```bash
API_BASE_URL=http://127.0.0.1:7860 \
  python3 -m streamlit run deployment/frontend_files/app.py --server.port 8501
```

Run the focused API contract tests after generating the model:

```bash
python3 -m unittest discover -s deployment/tests -v
```

## Local Docker smoke test

From the `prediction_submission` directory, start both containers on alternate
host ports to avoid colliding with existing local services:

```bash
BACKEND_HOST_PORT=8762 FRONTEND_HOST_PORT=8763 \
  docker compose -p superkart-local -f deployment/docker-compose.yml up --build -d
docker compose -p superkart-local -f deployment/docker-compose.yml ps
curl http://127.0.0.1:8762/health
curl -I http://127.0.0.1:8763/
python3 -m unittest discover -s deployment/tests -v
```

Open `http://127.0.0.1:8763/`, confirm the API status, submit a single
prediction, then upload `sourceData/Batch_Data_SuperKart.csv` in the batch tab.
The supplied batch should return eight predictions and two row-level errors
for its unsupported `Supermarket Type3` values. Stop only this Compose project
when finished:

```bash
docker compose -p superkart-local -f deployment/docker-compose.yml down
```

The single-prediction API accepts the ten engineered columns shown by
`sourceData/Batch_Data_SuperKart.csv` as JSON at `POST /v1/predict`. Batch
inference accepts a CSV in a multipart `file` field at `POST
/v1/predictbatch`. Each unsupported row is reported by its one-based row number;
the supplied batch has two rows with a store type absent from training.

## GitHub Codespaces containers

The repository includes `../.devcontainer/devcontainer.json`. In a Codespace it
builds and starts the Compose stack on creation, then restarts it when the
Codespace resumes. Port 8501 is the public Streamlit interface; port 7860 is
kept private because the frontend calls the backend over the Docker network.
If the Codespaces port panel does not apply the configured visibility, set
8501 to **Public** and leave 7860 **Private**.

Verify the forwarded Streamlit URL, then test the single form and batch upload
through that browser URL. Use the supplied model-ready batch file or download
the one-row model-input template in the app. Capture separate screenshots of
the completed single prediction and batch results, with the forwarded UI URL
visible. Record only the actual forwarded URL in the final submission; do not
guess it from the Codespace name.

Keep GitHub credentials in the account/Codespaces secret manager; do not add
tokens to source, notebooks, HTML, or logs.

To avoid conflicting with existing local services, the published host ports can
be changed with `BACKEND_HOST_PORT` and `FRONTEND_HOST_PORT`; the container
ports remain 7860 and 8501.
