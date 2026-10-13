"use strict";
const form = document.getElementById("calculator");
const message = document.getElementById("message");
const results = document.getElementById("results");
const exportButton = document.getElementById("export");
let mostRecent = null;
const round = (x, n = 3) => x === null ? "Not estimated" : Number(x).toFixed(n);
function render(data, sessions) {
  document.getElementById("spktv").textContent = round(data.spktv);
  document.getElementById("urr").textContent = round(data.urr, 1) + "%";
  document.getElementById("ektv").textContent = round(data.ektv);
  document.getElementById("stdktv").textContent = round(data.stdktv);
  document.getElementById("npcr").textContent = round(data.npcr);
  document.getElementById("assessment").textContent = (
    data.passesMinimum ? "Meets the selected schedule's minimum" : "Below the selected schedule's minimum"
  ) + (data.reachesTarget ? "; reaches the recommended target." : "; below the recommended target.");
  document.getElementById("thresholds").textContent = sessions === 3
    ? "Thrice-weekly HD: spKt/V minimum 1.2, target 1.4. URR ≥65% is a supplementary screening measure."
    : "Other HD schedules: weekly stdKt/V minimum 2.1, target 2.3. Residual renal clearance not included.";
  document.getElementById("npcr-note").textContent = sessions === 3
    ? "nPCR is a two-point estimate assuming negligible residual renal urea clearance. It depends on sample timing and metabolic stability."
    : "nPCR is intentionally not estimated for schedules other than three sessions per week.";
  message.textContent = "Estimate generated locally. These values are not a treatment prescription.";
  message.className = "notice success";
  results.hidden = false;
  exportButton.disabled = false;
}
form.addEventListener("submit", (event) => {
  event.preventDefault();
  message.className = "notice";
  results.hidden = true;
  exportButton.disabled = true;
  mostRecent = null;
  try {
    const values = Object.fromEntries(
      ["pre", "post", "hours", "uf", "weight", "sessions"].map(name => [
        name, Number(form.elements.namedItem(name).value)
      ])
    );
    for (const name of ["pre", "post", "hours", "uf", "weight", "sessions"]) {
      if (form.elements.namedItem(name).value.trim() === "") throw new RangeError("All measurements are required");
    }
    values.position = form.elements.namedItem("position").value;
    const result = KtV.calculate(values);
    mostRecent = { inputs: values, results: result,
      disclaimer: "Research/education estimate only; not a clinical prescription." };
    render(result, values.sessions);
  } catch (error) {
    message.textContent = "Cannot calculate: " + error.message;
    message.className = "notice error";
  }
});
form.addEventListener("reset", () => {
  mostRecent = null;
  results.hidden = true;
  exportButton.disabled = true;
  message.textContent = "Enter measurement values to estimate dialysis adequacy.";
  message.className = "notice";
});
exportButton.addEventListener("click", () => {
  if (!mostRecent) return;
  const blob = new Blob([JSON.stringify(mostRecent, null, 2) + "\n"],
    { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "dialysis-adequacy-estimate.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});
