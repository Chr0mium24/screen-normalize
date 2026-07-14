from dataclasses import asdict
from pathlib import Path

import pytest

from screen_normalize.experiments.runner import _method_args, method_config


def test_method_configs_are_distinct() -> None:
    frame_wise = method_config("frame_wise")
    flow = method_config("optical_flow")
    proposed = method_config("proposed")
    assert frame_wise.tracker == "detect" and not frame_wise.interpolate
    assert flow.tracker == "flow" and not flow.geometry_gate
    assert proposed.tracker == "reference" and proposed.interpolate and proposed.reference_align


def test_unknown_method() -> None:
    with pytest.raises(ValueError):
        method_config("unknown")


def _functional_differences(left: str, right: str) -> set[str]:
    ignored = {"method", "ablation_of", "disabled_module"}
    left_config = asdict(method_config(left))
    right_config = asdict(method_config(right))
    return {
        key
        for key in left_config
        if key not in ignored and left_config[key] != right_config[key]
    }


def test_ablation_configs_disable_only_the_target_module() -> None:
    assert _functional_differences("proposed", "no_reliability_gates") == {
        "geometry_gate",
        "reference_reliability_gates",
    }
    assert _functional_differences("proposed", "no_trajectory_smoothing") == {
        "smooth",
        "median_window",
        "trajectory_window",
    }
    assert _functional_differences("proposed", "no_offline_repair") == {"interpolate"}


def test_no_reliability_gates_makes_optional_thresholds_permissive() -> None:
    args = _method_args(Path("example.mp4"), method_config("no_reliability_gates"))
    assert not args.trajectory_geometry_gate
    assert args.reference_min_inliers == 1
    assert args.reference_min_inlier_ratio == 0.0
    assert args.reference_min_point_age == 1
    assert args.reference_min_coverage_x == 0.0
    assert args.reference_min_coverage_y == 0.0
    assert args.reference_max_scale_step == 0.0
    assert args.reference_max_area_step == 0.0
    assert args.reference_align_min_accept_ratio == 0.0


def test_proposed_dynamic_profile_uses_soft_reliability_gates() -> None:
    args = _method_args(Path("example.mp4"), method_config("proposed"))
    assert args.reference_min_inliers == 24
    assert args.reference_min_inlier_ratio == 0.15
    assert args.reference_max_reprojection_error == 4.5
    assert args.reference_max_scale_step == 0.08
    assert args.reference_max_area_step == 0.18
    assert args.reference_min_point_age == 1
    assert args.reference_min_coverage_x == 0.08
    assert args.reference_min_coverage_y == 0.05


def test_smoothing_and_repair_ablation_arguments_are_isolated() -> None:
    no_smoothing = _method_args(Path("example.mp4"), method_config("no_trajectory_smoothing"))
    assert no_smoothing.smooth == 0.0
    assert no_smoothing.median_window == 1
    assert no_smoothing.trajectory_window == 1
    assert no_smoothing.trajectory_interpolate
    assert no_smoothing.trajectory_geometry_gate

    no_repair = _method_args(Path("example.mp4"), method_config("no_offline_repair"))
    assert not no_repair.trajectory_interpolate
    assert no_repair.median_window == method_config("proposed").median_window
    assert no_repair.trajectory_window == method_config("proposed").trajectory_window
    assert no_repair.trajectory_geometry_gate
