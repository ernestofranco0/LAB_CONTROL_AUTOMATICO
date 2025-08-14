from utils.pid_controller import PIDController

pid_h1 = PIDController(Kp = 0, Ki = 0, Kd = 0, setpoint = 0, dt = 1.0, anti_windup_gain = 0)
pid_h2 = PIDController(Kp = 0, Ki = 0, Kd = 0, setpoint = 0, dt = 1.0, anti_windup_gain = 0)
PID_H1 = PIDController(Kp = 0, Ki = 0, Kd = 0, setpoint = 0, dt = 1.0, anti_windup_gain = 0)
PID_H2 = PIDController(Kp = 0, Ki = 0, Kd = 0, setpoint = 0, dt = 1.0, anti_windup_gain = 0)