"""
Software-only bash script runner for Sagebrush.

A Dripline Entity that overrides ``on_set`` to execute a local bash
script whenever a message is received.  The script path is set in the
YAML runtime config; the script itself is mounted into the container
at deploy time (e.g. via a Docker Swarm volume bind-mount).
"""

import subprocess
import os
import json
import logging

from dripline.core import calibrate
from dripline.core import Entity
from dripline.core import ThrowReply

logger = logging.getLogger(__name__)

__all__ = ['BashScriptRunner']


class BashScriptRunner(Entity):
    """
    A Dripline endpoint that runs a local bash script on every ``on_set``.

    Configuration parameters (set in the YAML runtime config):
        script_path (str, required):
            Absolute path to the bash script to execute.
        timeout (int, optional):
            Max execution time in seconds.  Default 30.
        pass_via (str, optional):
            How to pass the incoming value to the script:

            - ``"env"`` (default) — set as ``$DRIPLINE_VALUE``.
            - ``"stdin"``  — piped to the script's stdin.
            - ``"arg"``    — passed as the first positional argument.
    """

    def __init__(self, script_path=None, timeout=30, pass_via='env', **kwargs):
        Entity.__init__(self, **kwargs)
        if script_path is None:
            raise ValueError(
                "'script_path' is required for BashScriptRunner endpoint "
                f"'{self.name}'"
            )
        self._script_path = script_path
        self._timeout = int(timeout)
        self._pass_via = pass_via
        self._last_result = None

    @calibrate()
    def on_get(self):
        """Return the result of the most recent script execution."""
        logger.info("BashScriptRunner on_get for '%s'", self.name)
        return self._last_result

    def on_set(self, new_value):
        """
        Receive a Dripline message, execute the configured bash script,
        and store the result.
        """
        logger.info(
            "BashScriptRunner on_set for '%s' — running %s",
            self.name, self._script_path,
        )

        # Ensure the script exists and is executable.
        if not os.path.isfile(self._script_path):
            raise ThrowReply(
                'resource_error',
                f"Script not found: {self._script_path}",
            )
        if not os.access(self._script_path, os.X_OK):
            logger.warning(
                "Script %s is not executable — attempting chmod +x",
                self._script_path,
            )
            try:
                os.chmod(self._script_path, 0o755)
            except OSError as exc:
                raise ThrowReply(
                    'resource_error',
                    f"Cannot make script executable: {self._script_path} — {exc}",
                )

        # Serialise incoming value to JSON for consistent hand-off.
        json_value = json.dumps(new_value, default=str)

        # Build environment.
        run_env = os.environ.copy()
        run_env['DRIPLINE_VALUE'] = json_value

        # Build command and stdin plumbing.
        if self._pass_via == 'stdin':
            proc_kwargs = dict(input=json_value, text=True)
            cmd = ['/bin/bash', self._script_path]
        elif self._pass_via == 'arg':
            proc_kwargs = dict(text=True)
            cmd = ['/bin/bash', self._script_path, json_value]
        else:  # 'env'
            proc_kwargs = dict(text=True)
            cmd = ['/bin/bash', self._script_path]

        logger.debug("Running: %s", cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self._timeout,
                env=run_env,
                **proc_kwargs,
            )
        except subprocess.TimeoutExpired:
            logger.error(
                "Script %s timed out after %ds",
                self._script_path, self._timeout,
            )
            self._last_result = {
                'stdout': '',
                'stderr': f'Script timed out after {self._timeout}s',
                'returncode': -1,
                'timed_out': True,
            }
            return "Script timed out"
        except Exception as exc:
            raise ThrowReply(
                'resource_error',
                f"Failed to execute script {self._script_path}: {exc}",
            )

        self._last_result = {
            'stdout': result.stdout.strip() if result.stdout else '',
            'stderr': result.stderr.strip() if result.stderr else '',
            'returncode': result.returncode,
            'timed_out': False,
        }

        logger.info(
            "Script %s finished with returncode %d",
            self._script_path, result.returncode,
        )

        # Return stdout on success, stderr otherwise.
        if result.returncode == 0:
            return self._last_result['stdout']
        else:
            return self._last_result['stderr']
