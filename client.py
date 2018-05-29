from udp_client import UDPClient
from joystick import Joystick


class Client:
    def __init__(self):
        self.udp_client = UDPClient()
        self.joystick = Joystick()

    @classmethod
    def adapt(cls):
        pass

    def update(self):
        self.joystick.update()
        left_pwm = self.adapt(self.joystick.axis.get(1, 0))
        right_pwm = self.adapt(self.joystick.axis.get(4, 0))
        self.udp_client.write("%.2f,%.2f" % (left_pwm, right_pwm))
