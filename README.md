# Thyroid Ultrasound TI-RADS Agent

A deterministic ACR TI-RADS (2017) calculator for **manually entered adult thyroid ultrasound features**, with an offline browser interface, Python CLI, and FastAPI endpoint.

## Clinical scope

The calculator sums composition, echogenicity, shape, margins, and applicable echogenic foci. The total maps to TR1–TR5. The maximum nodule diameter is then compared with ACR follow-up and FNA thresholds:

| Category | Total points | Follow-up from | FNA from |
| --- | ---: | ---: | ---: |
| TR1 | 0 | Not routinely indicated | Not routinely indicated |
| TR2 | 2 | Not routinely indicated | Not routinely indicated |
| TR3 | 3 | 1.5 cm | 2.5 cm |
| TR4 | 4–6 | 1.0 cm | 1.5 cm |
| TR5 | ≥7 | 0.5 cm | 1.0 cm |

If a lesion is cystic/almost completely cystic or spongiform, the score is 0 and the other feature categories are not scored. Multiple echogenic foci are additive.

This is **decision support, not an image recognition model, a diagnosis, a validated medical device, or a clinical instruction to biopsy**. Decisions require ultrasound interpretation and individual patient context, including suspicious lymph nodes, history, previously biopsied nodules, and patient preferences. The 2017 ACR white paper is intended as guidance for adult patients.

Reference: Tessler FN et al. ACR TI-RADS Committee. *J Am Coll Radiol.* 2017;14:587–595. [DOI: 10.1016/j.jacr.2017.01.046](https://doi.org/10.1016/j.jacr.2017.01.046).

## Browser calculator

Open [web/index.html](web/index.html) directly in a current browser; it works without a web server, installation, Python, or network connectivity. Enter the largest nodule diameter in centimeters, select the relevant ultrasound descriptors, and click **Calculate TI-RADS**. View the points and management thresholds, or download the result as JSON.

All browser calculations take place locally. The browser calculator does not submit inputs to a server or use analytics. Avoid entering patient identifiers.

## Python and REST API

Python 3.10 or newer is required.

```bash
python -m pip install -e ".[test]"
python cli.py tirads --composition solid --size-cm 1.5 \
  --echogenicity hypoechoic --shape wider_than_tall --margin smooth
python cli.py serve --host 127.0.0.1 --port 8000
```

The package's installed CLI (`thyroid-ultrasound-ti-rads-engine`) also exposes a `tirads` subcommand. Both implementations share `thyroid_tirads_ai.tirads.score_tirads`.

Clinical scoring endpoint: `POST /api/ti-rads`.

```bash
curl -s http://127.0.0.1:8000/api/ti-rads \
  -H "Content-Type: application/json" \
  -d '{"composition":"solid","size_cm":1.5,"echogenicity":"hypoechoic","shape":"wider_than_tall","margin":"smooth","echogenic_foci":["punctate_foci"]}'
```

Accepted values:

- `composition`: `cystic`, `spongiform`, `mixed`, `solid`.
- `echogenicity`: `isoechoic_hyperechoic`, `hypoechoic`, `very_hypoechoic` (omit for cystic/spongiform).
- `shape`: `wider_than_tall`, `taller_than_wide` (omit for cystic/spongiform).
- `margin`: `smooth`, `ill_defined`, `lobulated_irregular`, `extrathyroidal_extension` (omit for cystic/spongiform).
- `echogenic_foci`: optional list containing `macrocalcifications`, `rim_calcifications`, `punctate_foci`; default empty.

`size_cm` must be a finite positive number. Invalid input returns HTTP 422.

## Legacy operational audit

The repository retains the older `agents/`, `thyroid_tirads_ai/`, and `enrichment.py` telemetry/audit workflows, including `audit`, `batch`, and `chat` commands and `POST /api/audit`. **These older generic threshold rules are not ACR TI-RADS scoring and must not be used for nodule management.** Their numerical warning/critical statuses are operational placeholders. The mock chat responder does not provide validated clinical advice.

```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
```

The backend retains dossiers in process memory and audit hashes in a process-local HMAC chain. It has heuristic identifier screening, **not comprehensive PHI detection, HIPAA certification, persistent records, or authenticated clinical access controls**. Avoid real patient data and do not expose the development backend on a public network.

## Tests

```bash
python -m pytest -q
python -m compileall -q agents thyroid_tirads_ai tests cli.py
node --test tests/test_web_tirads.cjs
```

CI tests Python 3.10–3.13 and the browser scoring module. Browser support targets current Chrome, Firefox, Safari, and Edge; manual cross-browser verification remains recommended.

## Deployment

The offline calculator is static HTML/JavaScript in `web/` and can be hosted on GitHub Pages without a backend. The Pages workflow publishes only `web/`; it does not deploy the Python APIs. The FastAPI backend can be run locally or in a Docker container via `docker build -t thyroid-tirads .` and `docker run -p 127.0.0.1:8000:8000 thyroid-tirads`.

## Technology and license

Python, FastAPI, Pydantic, standard-library clinical scoring; vanilla HTML, CSS, and JavaScript for the offline interface. [MIT License](LICENSE).
