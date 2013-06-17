import numpy as np
from cp2k import sbp

sbp.vebose = True

server = sbp.Server()

# ping pong
data = server.receive()
server.send(data)
