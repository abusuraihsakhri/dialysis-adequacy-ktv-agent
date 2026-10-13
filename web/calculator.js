/* Offline hemodialysis urea kinetics. Units: BUN mg/dL, t h, UF L, W kg.
   Reference: Daugirdas II; Leypoldt fixed-volume weekly stdKt/V;
   Depner-Daugirdas 1996 two-point nPCR for thrice-weekly HD. */
(function (root) {
  "use strict";
  const positive = (name, x) => {
    if (!Number.isFinite(x) || x <= 0) throw new RangeError(name + " must be positive and finite");
  };
  function calculate({ pre, post, hours, uf, weight, sessions = 3, position = "midweek" }) {
    [ ["Pre-BUN", pre], ["Post-BUN", post], ["Hours", hours], ["Weight", weight] ]
      .forEach(([name, value]) => positive(name, value));
    if (post >= pre) throw new RangeError("Post-BUN must be lower than pre-BUN");
    if (hours < 2 || hours > 24) throw new RangeError("Time must be between 2 and 24 hours");
    if (!Number.isFinite(uf) || uf < 0) throw new RangeError("UF must be finite and nonnegative");
    if (!Number.isInteger(sessions) || sessions < 1 || sessions > 7)
      throw new RangeError("Sessions must be a whole number from 1 to 7");
    const R = post / pre, argument = R - 0.008 * hours;
    if (argument <= 0) throw new RangeError("R − 0.008 × time must be positive");
    const spktv = -Math.log(argument) + (4 - 3.5 * R) * (uf / weight);
    if (!Number.isFinite(spktv) || spktv <= 0) throw new RangeError("Calculated spKt/V is invalid");
    const urr = 100 * (1 - R);
    const ektv = spktv - 0.6 * spktv / hours + 0.03;
    const f = -Math.expm1(-ektv);
    const denominator = f / ektv + 168 / (sessions * hours) - 1;
    if (ektv <= 0 || denominator <= 0) throw new RangeError("Kinetic model outside valid domain");
    const stdktv = (168 * f / hours) / denominator;
    let npcr = null;
    if (sessions === 3) {
      const coefs = {
        beginning: [36.3, 5.48, 53.5],
        midweek: [25.8, 1.15, 56.4],
        end: [16.3, 4.30, 56.6]
      };
      if (!Object.prototype.hasOwnProperty.call(coefs, position))
        throw new RangeError("Invalid session position");
      const [a, b, c] = coefs[position];
      npcr = pre / (a + b * spktv + c / spktv) + 0.168;
    }
    return {
      spktv, urr, ektv, stdktv, npcr, R,
      passesMinimum: sessions === 3 ? spktv >= 1.2 : stdktv >= 2.1,
      reachesTarget: sessions === 3 ? spktv >= 1.4 : stdktv >= 2.3
    };
  }
  root.KtV = { calculate };
  if (typeof module !== "undefined" && module.exports) module.exports = root.KtV;
})(typeof globalThis !== "undefined" ? globalThis : this);
