"""Simple Binary Protocol"""

import socket
import numpy as np


verbose = False


class SBPError(Exception):
    pass


class Container:
    """A representation of the SBP data kind and the number of items."""

    #
    # protocol settings
    #

    # endian of the data
    _endian = '<'

    # allowed data types
    _strings = ('i' + str(1), # byte
                'i' + str(1), # character
                'i' + str(4), # int32
                'f' + str(8), # float64
               )

    # data types for the header
    _int_kind_size = 4
    _int_len_size = 8
    header_size = _int_kind_size + _int_len_size
    _int_kind = np.dtype(_endian + 'i' + str(_int_kind_size))
    _int_len = np.dtype(_endian + 'i' + str(_int_len_size))

    #
    # methods
    #

    @classmethod
    def from_data(cls, data):
        """Construct the appropriate Container for `data`,
        raise SBPError is this is not possible."""

        # extract the data type
        if isinstance(data, np.ndarray):
            assert len(data.shape) == 1
            string = data.dtype.str[1:] # strip the endian
            try:
                code = cls._strings.index(string)
            except ValueError:
                raise SBPError, 'Array data type not supported by SBP: %s' % string
            n_items = data.shape[0]
        elif isinstance(data, str):
            dtype = str
            code = 1
            n_items = len(data)
        else:
            raise SBPError, 'Only numpy arrays and strings are supported by SBP.'

        return cls(code, n_items)

    @classmethod
    def from_header(cls, header):
        """Parse `header` and construct the appropriate Container."""

        code = np.fromstring(header[:cls._int_kind_size], dtype=cls._int_kind).item()
        cls.check_code(code)
        n_bytes = np.fromstring(header[cls._int_kind_size:], dtype=cls._int_len).item()
        return cls(code, n_bytes, is_byte_count=True)

    @classmethod
    def check_code(cls, code):
        """Check whther `code` is valid, i.e. in the allowed range."""

        if not (code >=0 and code < len(cls._strings)):
            raise SBPError, 'Invalid SBP kind code passed requested: %s', str(code)

    def __init__(self, code, n, is_byte_count=False):
        """Construct the Container with the SBP kind given by `code`.
        If `is_byte_count` is True, `n` determines the number of bytes, otherwise
        it determines the number of data items.
        """

        self.check_code(code)

        self.code = code
        self.dtype = np.dtype(self._endian + self._strings[code])
        self.size = int(self.dtype.str[-1:])
        if is_byte_count:
            self.n_items = n / self.size
        else:
            self.n_items = n
        self.n_bytes = self.size * self.n_items

    def header(self):
        """Construct and return the SBP header for this Container."""

        n_bytes = self.n_items * self.size
        header = np.array(self.code, dtype=self._int_kind).tostring()
        header += np.array(n_bytes, dtype=self._int_len).tostring()

        return header

    def print_message(self, data=None):
        """Print the properties of the current container and optionally
        also the data passed in `data`."""

        print 'SBP | data type:', self.dtype
        print 'SBP | data type str:', self.dtype.str
        print 'SBP | data type size:', self.size
        print 'SBP | # of items:', self.n_items
        print 'SBP | # of bytes:', self.n_bytes
        if data is not None:
            print 'SBP | data:'
            print data
        else:
            print '<data not provided>'
        print


class Connection:
    """A Simple Binary Protocol connection.

    Do not instantiate this directly, use Server or Client.

    Relies on `conn` being provided in derived classes.
    """

    def __init__(self):
        """Do not instantiate directly."""

        if self.__class__ is Connection:
            raise RuntimeError

    def send(self, data):
        """Send `data` through the connection."""

        container = Container.from_data(data)

        if container.code == 1:   # it is a string
            data_str = data
        else:                     # it is an array
            data_str = data.tostring()

        # compose message
        msg = container.header()
        msg += data_str

        if verbose:
            print 'SBP | send:'
            container.print_message(data)

        # send data
        self.conn.send(msg)

    def receive(self):
        """Receive from the connection and return the data."""

        # receive the header
        header = self.conn.recv(Container.header_size)

        # TODO: how to handle problems here?
        if header == '':
            raise RuntimeError

        container = Container.from_header(header)

        # TODO: use just one buffer and reinterpret the received data

        # receive the actual data
        data_str = self.conn.recv(container.n_bytes)

        # interpret data
        if container.code > 1:
            data = np.fromstring(data_str, container.dtype)
        else:
            data = data_str

        if verbose:
            print 'SBP | receive:'
            container.print_message(data)

        return data


class Server(Connection):
    """A Simple Binary Protocol server.

    Most functionality is implemented in Connection.
    """

    def __init__(self, host='localhost', port=4329):
        """Start listening at host:port and wait for a connection."""

        Connection.__init__(self)

        # open the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(1)

        print 'DBG | listening...'

        # accept the connection and print info
        self.conn, self.addr = s.accept()
        self.s = s

        if verbose:
            print 'Accepted connection from: %s:%d' % self.addr
            print


class Client(Connection):
    """A Simple Binary Protocol client.

    Most functionality is implemented in Connection.
    """

    def __init__(self, host='localhost', port=4329):
        """Connect to the socket at host:port."""

        Connection.__init__(self)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        if verbose:
            print 'Connected to: %s:%s' % (host, port)

        self.conn = s
