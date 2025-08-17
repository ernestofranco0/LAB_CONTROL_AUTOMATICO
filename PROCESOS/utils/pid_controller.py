class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint=0, dt=1.0, anti_windup_gain=0.0, output_limits=(0, 0.999)):

        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint

        self.dt = dt
        self.integral = 0
        self.prev_error = 0
        self.anti_windup_gain = anti_windup_gain

        self.output_limits = output_limits
        self.last_output = 0

    def reset(self):

        self.integral = 0
        self.prev_error = 0
        self.last_output = 0

    def compute(self, measurement):
        error = self.setpoint - measurement

        # Derivada y error previo
        derivative = (error - self.prev_error) / self.dt

        # Acumulador de la integral
        self.integral += error * self.dt

        # PID antes del clamping
        u = self.Kp * error + self.Ki * self.integral + self.Kd * derivative

        # Aplicar límites
        u_clamped = max(self.output_limits[0], min(u, self.output_limits[1]))

        # Anti-windup: corregir la integral si hubo clamping
        if self.anti_windup_gain > 0:
            self.integral += self.anti_windup_gain * (u_clamped - u)

        self.prev_error = error
        self.last_output = u_clamped
        return u_clamped

    def setParams(self, setKp, setKi, setKd, newSetPoint, setAntiWindupGain):

        self.Kp = setKp
        self.Ki = setKi
        self.Kd = setKd
        self.setpoint = newSetPoint
        self.anti_windup_gain = setAntiWindupGain
