import logging

from dripline.core import RequestSender, Service, ThrowReply


logger = logging.getLogger(__name__)

__all__ = ["SAGCoordinator"]


class SAGCoordinator(Service):
    def __init__(
        self,
        safe_attenuation=90,
        lo1_frequency=7444230,
        lo_power=13,
        arb_frequency=50,
        arb_power=-25,
        arb_power_units="DBM",
        arb_function="USER",
        arb_waveform_name="MAXWELLIAN",
        calibration_receiver_state="sag",
        post_calibration_receiver_state="bypass_ch1",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.requests = RequestSender(self, timeout_s=30)
        self.safe_attenuation = float(safe_attenuation)
        self.lo1_frequency = float(lo1_frequency)
        self.lo_power = float(lo_power)
        self.arb_frequency = float(arb_frequency)
        self.arb_power = float(arb_power)
        self.arb_power_units = arb_power_units
        self.arb_function = arb_function
        self.arb_waveform_name = arb_waveform_name
        self.calibration_receiver_state = calibration_receiver_state
        self.post_calibration_receiver_state = post_calibration_receiver_state

    def _set(self, endpoint, value):
        logger.info("setting %s to %r", endpoint, value)
        return self.requests.set(endpoint, value, timeout_s=30)

    def _safe_hardware(self):
        failures = []
        for endpoint, value in (
            ("sag_attenuator_value", self.safe_attenuation),
            ("sag_arb_output_status", "off"),
            ("sag_lo1_output_status", "off"),
            ("sag_lo2_output_status", "off"),
            ("wp_input", "term"),
        ):
            try:
                self._set(endpoint, value)
            except Exception as error:
                logger.exception("failed to place %s in its safe state", endpoint)
                failures.append(f"{endpoint}: {error}")
        if failures:
            raise ThrowReply("resource_error", "; ".join(failures))

    def safe(self):
        """Disable SAG outputs, maximize attenuation, and terminate the weak-port path."""
        self._safe_hardware()
        return {"state": "term", "safe_attenuation": self.safe_attenuation}

    def configure_injection(self, sag_frequency, sag_attenuator_value, **_kwargs):
        """Configure frequency and attenuation while all SAG outputs remain disabled."""
        attenuation = float(sag_attenuator_value)
        frequency = float(sag_frequency)
        if not 0 <= attenuation <= self.safe_attenuation:
            raise ThrowReply("invalid_value", f"attenuation must be between 0 and {self.safe_attenuation} dB")
        if frequency <= 10.69423e6:
            raise ThrowReply("invalid_value", "sag_frequency must exceed 10.69423 MHz")

        self._safe_hardware()
        try:
            self._set("sag_lo2_freq", frequency - 10.69423e6)
            self._set("sag_attenuator_value", attenuation)
        except Exception:
            self._safe_hardware()
            raise
        return {"configured": True, "sag_frequency": frequency, "attenuation": attenuation}

    def enable_sag(self, confirmation=None):
        """Route the receiver and weak-port paths, then enable SAG outputs."""
        if confirmation != "ENABLE_SAG_OUTPUT":
            raise ThrowReply("invalid_value", "confirmation must be ENABLE_SAG_OUTPUT")
        try:
            self._set("sag_lo1_freq", self.lo1_frequency)
            self._set("sag_lo1_power", self.lo_power)
            self._set("sag_lo2_power", self.lo_power)
            self._set("sag_arb_freq", self.arb_frequency)
            self._set("sag_arb_power_units", self.arb_power_units)
            self._set("sag_arb_power", self.arb_power)
            self._set("sag_arb_func", self.arb_function)
            self._set("sag_arb_func_user", self.arb_waveform_name)
            self._set("ch1_receiver_switch_state", self.calibration_receiver_state)
            self._set("wp_input", "sag")
            self._set("sag_lo2_output_status", "on")
            self._set("sag_lo1_output_status", "on")
            self._set("sag_arb_output_status", "on")
        except Exception:
            self._safe_hardware()
            self._set("ch1_receiver_switch_state", self.post_calibration_receiver_state)
            raise
        return {
            "state": "sag",
            "outputs_enabled": True,
            "receiver_switch_state": self.calibration_receiver_state,
        }

    def set_live_attenuation(self, attenuation, confirmation=None):
        """Change attenuation without changing SAG routing or output state."""
        if confirmation != "SAG_OUTPUT_ACTIVE":
            raise ThrowReply("invalid_value", "confirmation must be SAG_OUTPUT_ACTIVE")
        attenuation = float(attenuation)
        if not 0 <= attenuation <= self.safe_attenuation:
            raise ThrowReply("invalid_value", f"attenuation must be between 0 and {self.safe_attenuation} dB")
        self._set("sag_attenuator_value", attenuation)
        return {"attenuation": attenuation, "outputs_enabled": True}

    def finish_calibration(self):
        """Disable SAG hardware and return the receiver switch to its configured bypass state."""
        self._safe_hardware()
        try:
            self._set("ch1_receiver_switch_state", self.post_calibration_receiver_state)
        except Exception:
            logger.exception("failed to restore the receiver switch after SAG calibration")
            raise
        return {
            "state": "term",
            "safe_attenuation": self.safe_attenuation,
            "receiver_switch_state": self.post_calibration_receiver_state,
        }

    def update_state(self, new_state):
        """Compatibility command limited to non-output states."""
        if new_state == "term":
            return self.safe()
        if new_state == "vna":
            self._safe_hardware()
            self._set("wp_input", "vna")
            return {"state": "vna", "outputs_enabled": False}
        if new_state == "sag":
            raise ThrowReply("invalid_value", "use enable_sag with confirmation=ENABLE_SAG_OUTPUT")
        raise ThrowReply("invalid_value", f"unknown SAG state: {new_state}")