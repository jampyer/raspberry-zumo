require_relative 'gpio'
require_relative 'udp_server'


class Service
  DEADZONE = 4000
  def initialize
    @gpio = GPIO.new
    @socket = UDPServer.new
  end

  def adapt value
    if value >= DEADZONE
      [(value - DEADZONE) * 100.0 / (32767 - DEADZONE), 100.0].min
    else
      0.0
    end
  end

  def update
    axes = @socket.read.split(',').collect &:to_i
    @gpio.update adapt(axes[1]), adapt(-axes[1]), adapt(axes[0]), adapt(-axes[0])
  end

  def stop
    @gpio.stop
  end
end


if __FILE__ == $0
  service = Service.new
  Signal.trap "INT" do
    service.stop
    exit
  end
  while true
    service.update
  end
end