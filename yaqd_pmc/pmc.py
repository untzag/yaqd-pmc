#! /usr/bin/env python3
import asyncio

import mcapi
from yaqd_core import hardware


class PmcMotorDaemon(hardware.ContinuousHardwareDaemon):
    defaults = {
        "counts_per_mm": 58200,
        "controller": 0,
        "axis": 0,
        "tolerance": 20,
        "acceleration": 70000.0,
        "gain": 2211.0,
        "velocity": 11000.0,
        "integral_gain": 0,
        "integration_limit": 0,
        "integration_option": 0,
        "derivative_gain": 6000.0,
        "derivative_sample": 0.001364,
        "following_error": 0.0,
        "velocity_gain": 0.0,
        "accel_gain": 0.0,
        "decel_gain": 0.0,
        "encoder_scaling": 0.0,
        "update_rate": 0.0,
        "position_deadband": 0.0,
        "delay_at_target": 0.0,
        "output_offset": 0.0,
        "output_deadband": 0.0,
        # "enable_backlash_correction": False,
        # "backlash": 1000,
    }

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self.controller = mcapi.Mcapi()
        self.axis = config["axis"]
        self.controller.open(config["controller"], 1)
        self.controller.EnableAxis(self.axis, True)

        self.tolerance = config["tolerance"]
        # self.backlash_enabled = config["enable_backlash_correction"]
        # self.backlash = config["backlash"]
        # self.backlashing = False

        self.filter = self._get_filter(config)
        self.controller.SetFilterConfigEx(self.axis, self.filter)
        self.controller.SetAcceleration(self.axis, config["acceleration"])
        self.controller.SetGain(self.axis, config["gain"])
        self.controller.SetVelocity(self.axis, config["velocity"])

    def _get_filter(self, config):
        filt = mcapi.MCFILTEREX()
        filt.Gain = config["gain"]
        filt.IntegralGain = config["integral_gain"]
        filt.IntegrationLimit = config["integration_limit"]
        filt.IntegralOption = config["integral_option"]
        filt.DerivativeGain = config["derivative_gain"]
        filt.DerSamplePeriod = config["derivative_sample"]
        filt.FollowingError = config["following_errof"]
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
        self.controller.MoveAbsolute(self.axis, position)

    async def update_state(self):
        overflow = b""
        while True:
            self._busy = not self.controller.IsStopped(self.axis, 3)
            self._position = self.controller.GetPositionEx(self.axis)
            _, _, lo, hi = self.controller.GetLimits(self.axis)
            self._limits = [(lo, hi)]
            await self._busy.wait()

    def stop(self):
        self.ctrl.Stop(self.axis)

    def get_FollowingError(self):
        return self.ctrl.GetFollowingError(self.axis)

    def get_target(self):
        return self.ctrl.GetTargetEx(self.axis)

    def at_target(self):
        return self.ctrl.IsAtTarget(self.axis, 3)


if __name__ == "__main__":
    PmcMotorDaemon.main()
