require 'socket'


class Server
  def initialize host = 'raspberrypi', port = 2200
    @socket = UDPSocket.new
    @socket.bind host, port
  end

  def read
    reply, from = @socket.recvfrom 20
    reply
  end
end


Server.new.read
