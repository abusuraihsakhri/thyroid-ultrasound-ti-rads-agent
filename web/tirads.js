/* ACR TI-RADS 2017 adult nodule scoring; no external services. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.TIRADS = api;
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";
  const composition = { cystic: 0, spongiform: 0, mixed: 1, solid: 2 };
  const echogenicity = { isoechoic_hyperechoic: 1, hypoechoic: 2, very_hypoechoic: 3 };
  const shape = { wider_than_tall: 0, taller_than_wide: 3 };
  const margin = { smooth: 0, ill_defined: 0, lobulated_irregular: 2, extrathyroidal_extension: 3 };
  const foci = { macrocalcifications: 1, rim_calcifications: 2, punctate_foci: 3 };
  const plans = {
    TR3: { follow: 1.5, fna: 2.5, years: [1, 3, 5] },
    TR4: { follow: 1.0, fna: 1.5, years: [1, 2, 3, 5] },
    TR5: { follow: 0.5, fna: 1.0, years: [1, 2, 3, 4, 5] }
  };
  function validKey(table, key, field) {
    if (!Object.prototype.hasOwnProperty.call(table, key)) throw new Error("Invalid or missing " + field);
    return table[key];
  }
  function calculate(input) {
    if (!input || typeof input !== "object") throw new Error("Provide ultrasound descriptors");
    const size = input.size_cm;
    if (typeof size !== "number" || !Number.isFinite(size) || size <= 0) {
      throw new Error("Maximum nodule size must be a positive finite number (cm)");
    }
    const c = validKey(composition, input.composition, "composition");
    const selected = input.echogenic_foci === undefined ? [] : input.echogenic_foci;
    if (!Array.isArray(selected) || selected.some(k => !Object.prototype.hasOwnProperty.call(foci, k)) ||
        new Set(selected).size !== selected.length) throw new Error("Invalid or duplicate echogenic foci");
    let component_points;
    if (input.composition === "cystic" || input.composition === "spongiform") {
      if (input.echogenicity || input.shape || input.margin || selected.length) {
        throw new Error("Other features are not scored for cystic or spongiform nodules");
      }
      component_points = { composition: 0, echogenicity: 0, shape: 0, margin: 0, echogenic_foci: 0 };
    } else {
      component_points = {
        composition: c,
        echogenicity: validKey(echogenicity, input.echogenicity, "echogenicity"),
        shape: validKey(shape, input.shape, "shape"),
        margin: validKey(margin, input.margin, "margin"),
        echogenic_foci: selected.reduce((sum, key) => sum + foci[key], 0)
      };
    }
    const points = Object.values(component_points).reduce((a, b) => a + b, 0);
    let category, suspicion;
    if (points === 0) [category, suspicion] = ["TR1", "Benign"];
    else if (points === 2) [category, suspicion] = ["TR2", "Not suspicious"];
    else if (points === 3) [category, suspicion] = ["TR3", "Mildly suspicious"];
    else if (points >= 4 && points <= 6) [category, suspicion] = ["TR4", "Moderately suspicious"];
    else if (points >= 7) [category, suspicion] = ["TR5", "Highly suspicious"];
    else throw new Error("Impossible ACR TI-RADS score: check descriptors");
    const plan = plans[category];
    let management = "No routine FNA or follow-up by ACR TI-RADS";
    let followup_years = [];
    if (plan) {
      if (size >= plan.fna) management = "FNA threshold met";
      else if (size >= plan.follow) {
        management = "Ultrasound follow-up threshold met";
        followup_years = plan.years;
      } else management = "No routine FNA or follow-up by size criteria";
    }
    return {
      points, category, suspicion, component_points, size_cm: size, management,
      fna_threshold_cm: plan ? plan.fna : null,
      followup_threshold_cm: plan ? plan.follow : null,
      followup_years,
      note: "Decision support for adult nodules only; clinician judgement and clinical context take precedence.",
      reference: "ACR TI-RADS 2017; DOI 10.1016/j.jacr.2017.01.046"
    };
  }
  return { calculate };
});
