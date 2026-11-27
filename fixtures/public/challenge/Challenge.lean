import Mathlib.Analysis.Complex.HalfPlane
import Mathlib.Analysis.MellinTransform
import Mathlib.NumberTheory.LSeries.SumCoeff
import Mathlib.NumberTheory.LSeries.Nonvanishing
import Mathlib.NumberTheory.Harmonic.ZetaAsymp
import Mathlib.Analysis.Complex.BorelCaratheodory
import Mathlib.Analysis.Complex.HasPrimitives
import Mathlib.Analysis.Calculus.LogDeriv

open Complex Metric Set Filter MeasureTheory Asymptotics Topology ArithmeticFunction

theorem AlpogeRHCore1.zeroFreeRegion :
    ∃ c : ℝ, 0 < c ∧ ∀ s : ℂ, s ≠ 1 → 1-c/Real.log (|s.im|+2) ≤ s.re → riemannZeta s ≠ 0 := by
  sorry
