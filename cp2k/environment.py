import numpy as np


class Environment:
    """Represents a single force environment in a CP2K instance."""

    def __init__(self, env_id, conn):
        """Create the Environment object"""

        # cache the env_id
        self.env_id = env_id

        # CP2K Connection to communicate through
        self.conn = conn

        # cache the number of atoms, as it will not change
        self._n_atoms = self._get_n_atoms()

    def __del__(self):
        """Destroy also the corresponding force environment in the CP2K
        instance when deleting this object."""

        self.conn._destroy_env(self.env_id)

    def get_n_atoms(self):
        """ """

        return self._n_atoms

    def _get_n_atoms(self):
        """Return the number of atoms in this environment."""

        self.conn.conn.send('NATOM')
        # TODO: this should work but does not
        #self.conn.conn.send(np.array([self.env_id], dtype='int32'))
        data = self.conn.conn.receive()            # TODO: what is this?
        n = self.conn.conn.receive().item()
        self.conn.get_ready()

        return n

    def set_pos(self, pos):
        """Set the positions of this Environment to `pos`.

        :param pos: ndarray with new positions, 3xn shape
        """

        raise NotImplementedError

    def get_pos(self):
        """Return the position array of this Environment."""

        self.conn.conn.send('get_pos %i' % self.env_id)
        #self.conn.conn.send(np.array([self.env_id], dtype='int32'))
        data = self.conn.conn.receive()            # TODO: what is this?
        pos = self.conn.conn.receive()
        self.conn.get_ready()

        return pos.reshape((self._n_atoms, 3))

    def calc_E(self):
        """Calculate and return the potential energy of this Environment."""

        self.conn.conn.send('calc_e')
        #self.conn.conn.send(np.array([self.env_id], dtype='int32'))
        data = self.conn.conn.receive()            # TODO: what is this?
        E = self.conn.conn.receive().item()
        self.conn.get_ready()

        return E
