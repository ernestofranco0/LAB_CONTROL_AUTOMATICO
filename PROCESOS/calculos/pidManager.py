# calculos/pidManager.py
from utils.pid_controller import PIDController

# PIDs SOLO para u1 (h1) y u2 (h2). γ se ajusta manualmente.
pid_h1 = PIDController(Kp=0.3, Ki=0, Kd=0, setpoint=0, dt=1.0, anti_windup_gain=0)
pid_h2 = PIDController(Kp=0.3, Ki=0, Kd=0, setpoint=0, dt=1.0, anti_windup_gain=0)

def apply_params(kp, ki, kd, h1_ref, h2_ref, aw):
    # Asigna parámetros y reinicia integradores/derivadas
    pid_h1.Kp, pid_h1.Ki, pid_h1.Kd = kp, ki, kd
    pid_h1.setpoint = h1_ref
    pid_h1.anti_windup_gain = aw
    pid_h1.reset()

    pid_h2.Kp, pid_h2.Ki, pid_h2.Kd = kp, ki, kd
    pid_h2.setpoint = h2_ref
    pid_h2.anti_windup_gain = aw
    pid_h2.reset()