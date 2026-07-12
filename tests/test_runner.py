import pytest

from screen_normalize.experiments.runner import method_config


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
