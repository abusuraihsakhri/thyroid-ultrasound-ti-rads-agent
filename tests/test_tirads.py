"""Reference cases and boundary tests for the deterministic ACR TI-RADS calculator."""
import json

import pytest
from fastapi.testclient import TestClient

from thyroid_tirads_ai.tirads import score_tirads
from agents.api import app
from cli import main, parse_boolean

BASE = dict(
    composition="solid",
    echogenicity="isoechoic_hyperechoic",
    shape="wider_than_tall",
    margin="smooth",
    echogenic_foci=[],
)


@pytest.mark.parametrize("composition", ["cystic", "spongiform"])
def test_tr1_special_compositions(composition):
    result = score_tirads(composition=composition, size_cm=3.5)
    assert (result["points"], result["category"]) == (0, "TR1")
    assert result["management"].startswith("No routine FNA")


def test_tr2_mixed_isoechoic():
    result = score_tirads(**{**BASE, "composition": "mixed"}, size_cm=3)
    assert (result["points"], result["category"]) == (2, "TR2")


@pytest.mark.parametrize("category,extra,follow,fna,years", [
    ("TR3", {}, 1.5, 2.5, [1, 3, 5]),
    ("TR4", {"echogenicity": "hypoechoic"}, 1.0, 1.5, [1, 2, 3, 5]),
    ("TR5", {"echogenicity": "very_hypoechoic", "shape": "taller_than_wide"}, 0.5, 1.0, [1, 2, 3, 4, 5]),
])
def test_category_size_boundaries(category, extra, follow, fna, years):
    descriptors = {**BASE, **extra}
    small = score_tirads(**descriptors, size_cm=follow - 0.01)
    observed = score_tirads(**descriptors, size_cm=follow)
    biopsy = score_tirads(**descriptors, size_cm=fna)
    assert all(result["category"] == category for result in (small, observed, biopsy))
    assert small["management"] == "No routine FNA or follow-up by size criteria"
    assert observed["management"] == "Ultrasound follow-up threshold met"
    assert observed["followup_years"] == years
    assert biopsy["management"] == "FNA threshold met"
    assert biopsy["followup_years"] == []


def test_multiple_foci_are_additive():
    result = score_tirads(**{**BASE, "echogenic_foci": ["macrocalcifications", "rim_calcifications", "punctate_foci"]}, size_cm=1.0)
    assert result["component_points"]["echogenic_foci"] == 6
    assert result["points"] == 9
    assert result["category"] == "TR5"


@pytest.mark.parametrize("kwargs", [
    {**BASE, "size_cm": 0},
    {**BASE, "size_cm": float("nan")},
    {**BASE, "size_cm": float("inf")},
    {**BASE, "size_cm": True},
    {**BASE, "size_cm": 1, "shape": "invalid"},
    {**BASE, "size_cm": 1, "echogenic_foci": ["punctate_foci", "punctate_foci"]},
    {**BASE, "size_cm": 1, "echogenic_foci": ["invalid"]},
    {"composition": "cystic", "size_cm": 1, "echogenicity": "hypoechoic"},
])
def test_invalid_descriptors_rejected(kwargs):
    with pytest.raises(ValueError):
        score_tirads(**kwargs)


def test_api_scoring_and_validation():
    client = TestClient(app)
    response = client.post("/api/ti-rads", json={**BASE, "size_cm": 1.5})
    assert response.status_code == 200
    assert response.json()["category"] == "TR3"
    assert response.json()["management"] == "Ultrasound follow-up threshold met"
    assert client.post("/api/ti-rads", json={**BASE, "size_cm": -1}).status_code == 422
    assert client.post("/api/ti-rads", json={**BASE, "size_cm": 1, "margin": "invalid"}).status_code == 422


def test_package_api_scoring():
    from thyroid_tirads_ai.server import create_app
    client = TestClient(create_app())
    response = client.post("/api/ti-rads", json={"composition": "spongiform", "size_cm": 2.2})
    assert response.status_code == 200
    assert response.json()["category"] == "TR1"


def test_csv_boolean_parser_is_strict():
    assert parse_boolean("False") is False
    assert parse_boolean("TRUE") is True
    assert parse_boolean("0") is False
    with pytest.raises(ValueError):
        parse_boolean("perhaps")


def test_tirads_cli(capsys):
    assert main(["tirads", "--composition", "cystic", "--size-cm", "3"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["category"] == "TR1"
