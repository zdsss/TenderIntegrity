"""Unit tests for RiskSynthesizer"""
import pytest

from src.analysis.risk_synthesizer import RiskSynthesizer, CompositeRisk


class TestRiskSynthesizer:

    def setup_method(self):
        self.synth = RiskSynthesizer()

    # ── Helper builders ──────────────────────────────────────────────────

    def _overlap(self, field_type: str, overlap_type: str = "exact") -> dict:
        return {
            "field_type": field_type,
            "value_a": "test",
            "value_b": "test",
            "overlap_type": overlap_type,
            "risk_note": "test note",
        }

    def _rare(self, count: int, level: str) -> dict:
        return {"risk_level": level, "total_match_count": count}

    def _price(self, level: str, ratio: float | None = None) -> dict:
        return {
            "risk_level": level,
            "proximity_ratio": ratio,
            "is_price_coordinated": level != "none",
        }

    def _meta(self, level: str, clustered: bool = False, gap: float | None = None, notes: list | None = None) -> dict:
        return {
            "risk_level": level,
            "same_author": level == "high",
            "same_company": False,
            "is_timestamp_clustered": clustered,
            "time_gap_minutes": gap,
            "risk_notes": notes or [],
        }

    def _struct(self, score: float, level: str) -> dict:
        return {"overall_score": score, "structure_risk_level": level}

    # ── Tests ────────────────────────────────────────────────────────────

    def test_returns_composite_risk(self):
        result = self.synth.synthesize("low", 0.05, None, [], None, None, None)
        assert isinstance(result, CompositeRisk)
        assert result.final_level in ("high", "medium", "low")

    def test_text_only_low_stays_low(self):
        result = self.synth.synthesize("low", 0.05, None, [], None, None, None)
        assert result.final_level == "low"
        assert result.triggered_signals == []

    def test_text_only_high_stays_high(self):
        result = self.synth.synthesize("high", 0.45, None, [], None, None, None)
        assert result.final_level == "high"

    def test_exact_phone_overlap_forces_high(self):
        overlaps = [self._overlap("phone", "exact")]
        result = self.synth.synthesize("low", 0.05, None, overlaps, None, None, None)
        assert result.final_level == "high"
        assert any("电话" in s or "邮箱" in s for s in result.triggered_signals)

    def test_exact_email_overlap_forces_high(self):
        overlaps = [self._overlap("email", "exact")]
        result = self.synth.synthesize("low", 0.10, None, overlaps, None, None, None)
        assert result.final_level == "high"

    def test_team_member_exact_overlap_forces_high(self):
        overlaps = [self._overlap("team_member", "exact")]
        result = self.synth.synthesize("low", 0.05, None, overlaps, None, None, None)
        assert result.final_level == "high"

    def test_two_rare_matches_forces_high(self):
        result = self.synth.synthesize("low", 0.10, None, [], self._rare(2, "high"), None, None)
        assert result.final_level == "high"
        assert any("罕见序列" in s for s in result.triggered_signals)

    def test_one_rare_match_forces_medium(self):
        result = self.synth.synthesize("low", 0.05, None, [], self._rare(1, "medium"), None, None)
        assert result.final_level == "medium"

    def test_high_price_risk_forces_high(self):
        result = self.synth.synthesize("low", 0.05, None, [], None, self._price("high", 0.005), None)
        assert result.final_level == "high"
        assert any("报价" in s for s in result.triggered_signals)

    def test_medium_price_risk_forces_medium(self):
        result = self.synth.synthesize("low", 0.05, None, [], None, self._price("medium", 0.03), None)
        assert result.final_level == "medium"

    def test_meta_high_risk_forces_high(self):
        result = self.synth.synthesize("low", 0.05, None, [], None, None, self._meta("high", notes=["作者相同"]))
        assert result.final_level == "high"

    def test_timestamp_clustered_plus_text_rate_forces_medium(self):
        meta = self._meta("medium", clustered=True, gap=15.0, notes=["时间差15分钟"])
        result = self.synth.synthesize("low", 0.20, None, [], None, None, meta)
        assert result.final_level == "medium"

    def test_timestamp_clustered_low_text_rate_no_upgrade(self):
        meta = self._meta("medium", clustered=True, gap=15.0)
        result = self.synth.synthesize("low", 0.05, None, [], None, None, meta)
        # text_rate < 0.15 → no upgrade from timestamp alone
        assert result.final_level == "low"

    def test_high_structure_plus_high_text_rate_forces_high(self):
        struct = self._struct(75.0, "high")
        result = self.synth.synthesize("low", 0.35, struct, [], None, None, None)
        assert result.final_level == "high"
        assert any("结构分" in s for s in result.triggered_signals)

    def test_medium_structure_plus_fuzzy_overlap_forces_medium(self):
        struct = self._struct(55.0, "medium")
        overlaps = [self._overlap("company", "fuzzy")]
        result = self.synth.synthesize("low", 0.10, struct, overlaps, None, None, None)
        assert result.final_level == "medium"

    def test_multiple_signals_all_forces_high(self):
        overlaps = [self._overlap("phone", "exact")]
        rare = self._rare(3, "high")
        price = self._price("high", 0.005)
        result = self.synth.synthesize("low", 0.05, None, overlaps, rare, price, None)
        assert result.final_level == "high"
        assert len(result.triggered_signals) >= 2

    def test_signal_breakdown_populated(self):
        overlaps = [self._overlap("phone", "exact")]
        result = self.synth.synthesize("medium", 0.25, None, overlaps, None, None, None)
        breakdown = result.signal_breakdown
        assert "text" in breakdown
        assert "field_overlaps" in breakdown
        assert breakdown["field_overlaps"]["exact_phone_email_count"] == 1

    def test_forced_medium_with_text_high_becomes_high(self):
        # medium signal + text already high → should stay high
        result = self.synth.synthesize("high", 0.50, None, [], self._rare(1, "medium"), None, None)
        assert result.final_level == "high"
