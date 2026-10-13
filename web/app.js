"use strict";
const form = document.getElementById("nodule-form");
const composition = document.getElementById("composition");
const extra = document.getElementById("scored-features");
const output = document.getElementById("result");
const error = document.getElementById("error");
const download = document.getElementById("download");
let lastResult = null;

function updateComposition() {
  const benignComposition = ["cystic", "spongiform"].includes(composition.value);
  extra.disabled = benignComposition;
  document.getElementById("benign-help").hidden = !benignComposition;
}
function setResult(result) {
  document.getElementById("category").textContent = result.category;
  document.getElementById("points").textContent = String(result.points) + " points";
  document.getElementById("suspicion").textContent = result.suspicion;
  document.getElementById("management").textContent = result.management;
  const thresholds = document.getElementById("thresholds");
  if (result.fna_threshold_cm === null) {
    thresholds.textContent = "ACR TI-RADS: no routine FNA or ultrasound follow-up.";
  } else {
    thresholds.textContent =
      "FNA at ≥ " + result.fna_threshold_cm + " cm · Ultrasound follow-up at ≥ " +
      result.followup_threshold_cm + " cm.";
  }
  document.getElementById("schedule").textContent = result.followup_years.length
    ? "Suggested surveillance intervals: " + result.followup_years.join(", ") + " year(s), subject to clinical assessment."
    : "No surveillance schedule indicated for this size category.";
  document.getElementById("breakdown").textContent = Object.entries(result.component_points)
    .map(([name, score]) => name.replaceAll("_", " ") + ": " + score).join(" · ");
  output.hidden = false;
  download.disabled = false;
}
form.addEventListener("submit", event => {
  event.preventDefault();
  error.hidden = true;
  output.hidden = true;
  download.disabled = true;
  lastResult = null;
  const sizeInput = document.getElementById("size");
  const benign = ["cystic", "spongiform"].includes(composition.value);
  const input = {
    composition: composition.value,
    size_cm: Number(sizeInput.value),
    echogenicity: benign ? null : document.getElementById("echogenicity").value,
    shape: benign ? null : document.getElementById("shape").value,
    margin: benign ? null : document.getElementById("margin").value,
    echogenic_foci: benign ? [] : Array.from(document.querySelectorAll('input[name="foci"]:checked'), el => el.value)
  };
  try {
    if (sizeInput.value.trim() === "") throw new Error("Enter the maximum nodule diameter");
    lastResult = TIRADS.calculate(input);
    setResult(lastResult);
  } catch (err) {
    error.textContent = err.message;
    error.hidden = false;
  }
});
composition.addEventListener("change", () => {
  updateComposition();
  output.hidden = true;
  download.disabled = true;
});
form.addEventListener("change", () => {
  download.disabled = true;
  output.hidden = true;
  lastResult = null;
});
download.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "acr-ti-rads-result.json";
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
});
updateComposition();
