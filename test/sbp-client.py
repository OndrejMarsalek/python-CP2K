import numpy as np
from cp2k import sbp

sbp.verbose = True

a = np.arange(10, dtype=np.int32)

client = sbp.Client()

client.send(a)
b = client.receive()
assert (a == b).all()
