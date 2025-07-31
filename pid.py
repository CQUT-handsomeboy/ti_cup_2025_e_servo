class DefaultPID:
    def __init__(self, kp: float, ki: float, kd: float) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.P = 0
        self.I = 0  # 累加项
        self.D = 0
        self.error = 0
        self.prev_error = 0

    def __call__(self, input: float, target: float) -> float:
        self.error = target - input
        self.P = self.error * self.kp
        self.I += self.error * self.ki
        self.D = (self.error - self.prev_error) * self.kd
        self.prev_error = self.error
        output = self.I + self.D + self.P
        return output
