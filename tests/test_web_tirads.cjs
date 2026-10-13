"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculate } = require("../web/tirads.js");

const base = {
  composition: "solid",
  echogenicity: "isoechoic_hyperechoic",
  shape: "wider_than_tall",
  margin: "smooth",
  echogenic_foci: []
};

test("TR1 and TR2 reference combinations", () => {
  assert.equal(calculate({ composition: "cystic", size_cm: 3 }).category, "TR1");
  assert.equal(calculate({ composition: "spongiform", size_cm: 3 }).points, 0);
  assert.equal(calculate({ ...base, composition: "mixed", size_cm: 3 }).category, "TR2");
});

for (const [category, extra, follow, fna, years] of [
  ["TR3", {}, 1.5, 2.5, [1, 3, 5]],
  ["TR4", { echogenicity: "hypoechoic" }, 1.0, 1.5, [1, 2, 3, 5]],
  ["TR5", { echogenicity: "very_hypoechoic", shape: "taller_than_wide" }, 0.5, 1.0, [1, 2, 3, 4, 5]]
]) {
  test(category + " size thresholds", () => {
    const input = { ...base, ...extra };
    const below = calculate({ ...input, size_cm: follow - 0.01 });
    const observed = calculate({ ...input, size_cm: follow });
    const fnaResult = calculate({ ...input, size_cm: fna });
    assert.equal(observed.category, category);
    assert.equal(below.management, "No routine FNA or follow-up by size criteria");
    assert.equal(observed.management, "Ultrasound follow-up threshold met");
    assert.deepEqual(observed.followup_years, years);
    assert.equal(fnaResult.management, "FNA threshold met");
  });
}

test("All applicable echogenic foci are additive", () => {
  const result = calculate({
    ...base, size_cm: 1,
    echogenic_foci: ["macrocalcifications", "rim_calcifications", "punctate_foci"]
  });
  assert.equal(result.component_points.echogenic_foci, 6);
  assert.equal(result.points, 9);
  assert.equal(result.category, "TR5");
});

test("Input rejection and nonfinite sizes", () => {
  for (const size_cm of [0, -1, NaN, Infinity, "1"]) {
    assert.throws(() => calculate({ ...base, size_cm }));
  }
  assert.throws(() => calculate({ ...base, size_cm: 1, margin: "invalid" }));
  assert.throws(() => calculate({ ...base, size_cm: 1, echogenic_foci: ["punctate_foci", "punctate_foci"] }));
  assert.throws(() => calculate({ composition: "cystic", size_cm: 1, echogenicity: "hypoechoic" }));
});
