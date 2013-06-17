from cp2k.sbp import Server
from environment import Environment


class Connection:
    """Represents a connection to a CP2K instance.
 
    Uses the Simple Binary Protocol for the connection. Acts as a server
    accepting a connection from the CP2K instance.
    """

    def __init__(self, host='', port=4329):
        """Create the `Connection` object.
        
        Start an SBP server at the address `host` and port `port` and wait for
        a connection from a CP2K client.
        """

        # create the SBP server
        self.conn = Server(host, port)

        # read the ID
        self.id = self.conn.receive()

        # CP2K should be ready now
        self.get_ready()

    def __del__(self):
        """ """

        # TODO: terminate connection gracefully

    def get_ready(self):
        """Get the next message from the CP2K instance and expect it to be
        the ready signal."""

        msg = self.conn.receive()

        if msg != '* READY':
            raise RuntimeError, 'CP2K not ready, the message is: %s' % msg

    def create_env(self, input_fn):
        """Create a force environment in the CP2K instance. Create the
        corresponding Environment and return it."""

        self.conn.send('load %s' % input_fn)
        env_id = self.conn.receive().item()
        if env_id == -1:
            raise RuntimeError, 'Environment creation failed.'
        self.get_ready()

        return Environment(env_id, self)

    def _last_env_id(self):
        """Return the ID of the last environment created."""

        self.conn.send('last_env_id')
        env_id = self.conn.receive().item()

        return env_id

    def _destroy_env(self, env_id):
        """Destroy the environment given by ID."""

        self.conn.send('destroy %i' % env_id)
        data = self.conn.receive()            # TODO: what is this?
        self.get_ready()

    def get_units(self):
        """Return a string specifying the units of the results returned
        from this Connection."""

        self.conn.send('units')
        u = self.conn.receive()
        self.get_ready()

        return u

    def set_units_eV_A(self):
        """Returned results will have lengths in Angstrom
        and energies in eV."""

        self.conn.send('units_ev_a')
        self.get_ready()

    def set_units_au(self):
        """Returned results will be in atomic units."""

        self.conn.send('units_au')
        self.get_ready()
