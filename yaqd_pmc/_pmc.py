__all__ = ["PmcMotor"]

import asyncio
from typing import Dict, Any, List

from yaqd_core import ContinuousHardware

from . import mcapi


class PmcMotor(ContinuousHardware):
    _kind = "pmc"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self.controller = mcapi.Mcapi()
        self.axis = config["axis"]
        self.controller.Open(config["controller"], 1)
        self.controller.EnableAxis(self.axis, True)

        self.counts_per_mm = config["counts_per_mm"]
        self._units = config["units"]
        self.tolerance = config["tolerance"]
        # self.backlash_enabled = config["enable_backlash_correction"]
        # self.backlash = config["backlash"]
        # self.backlashing = False

        self.filter = self._get_filter(config)
        self.controller.SetFilterConfigEx(self.axis, self.filter)
        self.controller.SetAcceleration(self.axis, config["acceleration"])
        self.controller.SetGain(self.axis, config["gain"])
        self.controller.SetVelocity(self.axis, config["velocity"])

        if config["startup_behavior"] == "trust_state":
            self.reset_to_known_position(self._state["position"])

    def _get_filter(self, config):
        filt = mcapi.MCFILTEREX()
        filt.Gain = config["gain"]
        filt.IntegralGain = config["integral_gain"]
        filt.IntegrationLimit = config["integration_limit"]
        filt.IntegralOption = config["integration_option"]
        filt.DerivativeGain = config["derivative_gain"]
        filt.DerSamplePeriod = config["derivative_sample"]
        filt.FollowingError = config["following_error"]
        filt.VelocityGain = config["velocity_gain"]
        filt.AccelGain = config["accel_gain"]
        filt.DecelGain = config["decel_gain"]
        filt.EncoderScaling = config["encoder_scaling"]
        filt.UpdateRate = config["update_rate"]
        filt.PositionDeadband = config["position_deadband"]
        filt.DelayAtTarget = config["delay_at_target"]
        filt.OutputOffset = config["output_offset"]
        filt.OutputDeadband = config["output_deadband"]
        return filt

    def _set_position(self, position):
        self.controller.MoveAbsolute(self.axis, self.mm_to_steps(position))

    async def update_state(self):
        self._state["hw_limits"] = (0, 50)
        while True:
            self._state["position"] = self.steps_to_mm(self.controller.GetPositionEx(self.axis))
            self._busy = (
                abs(
                    self.mm_to_steps(self._state["position"])
                    - self.mm_to_steps(self._state["destination"])
                )
                > self.tolerance
            )
            try:
                await asyncio.wait_for(self._busy_sig.wait(), 0.1)
            except asyncio.TimeoutError:
                pass

    def stop(self):
        self.ctrl.Stop(self.axis)

    def steps_to_mm(self, steps):
        return self._state["hw_limits"][1] - steps / self.counts_per_mm

    def mm_to_steps(self, mm):
        return round((self._state["hw_limits"][1] - mm) * self.counts_per_mm)

    def reset_to_known_position(self, position):
        self.controller.SetPosition(self.axis, self.mm_to_steps(position))
        self._state["destination"] = position
