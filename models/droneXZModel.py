import casadi as ca
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from models.baseModel import BaseModel
from models.config import DroneXZConfig


"""
| DroneXZModel |
|<---l--->|
O---------x---------O
m(kg)  (px, pz)     m(kg)
fl------------------fr
The forces excerted by the left and right propellers are perpendicular to the drone.

x = (px, pz, pitch, vx, vz, vpitch)
a = (fl, fr)

\dot{px} = vx
\dot{pz} = vz
\dot{pitch} = vpitch
2m*\dot{vx} = - (fl + fr) * sin(pitch)
2m*\dot{vz} = -2m*g + (fl + fr)*cos(pitch)
4*m*l*l*\dot{vpitch} = (fr - fl) * l
"""

class DroneXZModel(BaseModel):
    def __init__(self, sampling_time):
        super().__init__(sampling_time)
        self.model_name = "DroneXZModel"
        self.model_config = DroneXZConfig()

        x = ca.MX.sym('x', self.model_config.nx)
        u = ca.MX.sym('u', self.model_config.nu)
        x_dot = ca.vertcat(
            x[3],  # \dot{px}
            x[4],  # \dot{pz}
            x[5],  # \dot{pitch}
            -(u[0] + u[1]) * ca.sin(x[2]) / (2 * self.model_config.mass),                   # \dot{vx}
            - self._gravity + (u[0] + u[1]) * ca.cos(x[2]) / (2 * self.model_config.mass),  # \dot{vz}
            (u[1] - u[0]) / (4 * self.model_config.mass * self.model_config.l)              # \dot{vpitch}
        )
        dae = {'x': x, 'p': u, 'ode': x_dot}
        opts = {'tf': self._sampling_time}
        self.I = ca.integrator('I', 'rk', dae, opts)


    def animateSimulation(self, x_trajectory, u_trajectory, additional_lines_or_scatters=None):
        sim_length = u_trajectory.shape[1]
        fig, ax = plt.subplots()
        for i in range(sim_length+1):
            ax.set_aspect('equal')
            ax.set_xlim(-1, 5)
            ax.set_ylim(-1, 5)
            ax.set_xlabel('px(m)', fontsize=14)
            ax.set_ylabel('pz(m)', fontsize=14)
            ax.set_title('Drone XZ Simulation')
            left_x = x_trajectory[0, i] - self.model_config.l * ca.cos(x_trajectory[2, i])
            left_z = x_trajectory[1, i] - self.model_config.l * ca.sin(x_trajectory[2, i])
            right_x = x_trajectory[0, i] + self.model_config.l * ca.cos(x_trajectory[2, i])
            right_z = x_trajectory[1, i] + self.model_config.l * ca.sin(x_trajectory[2, i])
            ax.plot(x_trajectory[0, :i+1], x_trajectory[1, :i+1], color="tab:gray", linewidth=2, zorder=0)
            ax.plot([left_x, right_x], [left_z, right_z], color="tab:blue", linewidth=5, zorder=1)
            ax.scatter(x_trajectory[0, i], x_trajectory[1, i], color="tab:gray", s=100, zorder=2)
            if i < sim_length:
                patch_fl = patches.Arrow(left_x, left_z, -0.1*u_trajectory[0, i]*ca.sin(x_trajectory[2, i]), 0.1*u_trajectory[0, i]*ca.cos(x_trajectory[2, i]), color="tab:green")
                patch_fr = patches.Arrow(right_x, right_z, -0.1*u_trajectory[1, i]*ca.sin(x_trajectory[2, i]), 0.1*u_trajectory[1, i]*ca.cos(x_trajectory[2, i]), color="tab:green")
                ax.add_patch(patch_fl)
                ax.add_patch(patch_fr)

            if additional_lines_or_scatters is not None:
                for key, value in additional_lines_or_scatters.items():
                    if value["type"] == "scatter":
                        ax.scatter(value["data"][0], value["data"][1], color=value["color"], s=value["s"], label=key, marker=value["marker"])
                    elif value["type"] == "line":
                        ax.plot(value["data"][0], value["data"][1], color=value["color"], linewidth=2, label=key)

            ax.set_title(f"Drone XZ Simulation: Step {i+1}")
            ax.legend()
            plt.show(block=False)
            plt.pause(0.5)
            ax.clear()
        return