class Cp2kConnection:
    """ """

    def __init__(self, task, task_dir):
        """Initiates a CP2K connection."""

        #my_dir = os.getcwd()
        #os.chdir(task_dir)
        #self.st=subprocess.Popen(task,
        #                         shell=True,
        #                         stdin=subprocess.PIPE,
        #                         stdout=subprocess.PIPE,
        #                         stderr=subprocess.STDOUT,
        #                         close_fds=1,
        #                         env=os.environ)
        self.is_ready = 0
        self.envs = {}
        self.n_errors = 0
        self.last_errors = []
        os.chdir(my_dir)

    def raise_last_error(self, n_errors=0):
        """ """

        if n_errors != self.n_errors:
            raise Exception(''.join(self.last_errors))

    def add_errors(self, errors):
        """Add the given errors to the task errors."""

        if errors:
            self.n_errors += 1
            self.last_errors = errors

    def clear_errors(self):
        """ """

        self.n_errors = 0
        self.last_errors = []

    def get_ready(self):
        """Read the readiness message of the subtask."""

        ready_re = re.compile(r"^ *\* *(?:ready).*",re.IGNORECASE)
        error_re = re.compile(r"^ *\* *error.*",re.IGNORECASE)
        lines = []
        errors = []
        while 1:
            line = self.st.stdout.readline()
            if not line:
                break
            if error_re.match(line):
                errors.append(line)
            if ready_re.match(line):
                self.is_ready = 1
                self.add_errors(errors)
                return lines
            lines.append(line)
        self.add_errors(errors)
        raise Exception('cp2k_shell did not get ready')

    def exec_cmd(self, cmd_str, async=0):
        """Execute a command and (if async) return the output."""

        if not self.is_ready:
            lines = self.get_ready()
        self.st.stdin.write(cmd_str)
        if cmd_str[-1] != '\n':
            self.st.stdin.write('\n')
        self.st.stdin.flush()
        if async:
            self.isReady = 0
        else:
            return self.get_ready()

    def new_env(self, input_file, run_dir=''):
        """Create a new environment and
        change the current working directory to it."""

        nerr = self.n_errors
        if run_dir and run_dir != '.':
            self.exec_cmd('cd '+run_dir)
        if self.n_errors == nerr:
            lines = self.exec_cmd('load '+input_file)
            if self.n_errors == nerr:
                env_id = int(lines[0])
                self.envs[env_id] = Cp2kEnvironment(self, env_id)
                return self.envs[env_id]
        return None

    def new_bg_env(self, input_file, run_dir=''):
        """Create a new environment in the background.
        Use last_env to get it."""

        nerr = self.n_errors
        if run_dir and run_dir != '.':
            self.exec_cmd('cd '+runDir)
        if self.n_errors == nerr:
            self.exec_cmd('bg_load '+input_file, async=1)

    def last_env(self):
        """Return the last environment created."""

        lines = self.exec_cmd('last_env_id')
        env_id = int(lines[0])
        if env_id <= 0:
            return None
        if not self.envs.has_key(env_id):
            self.envs[env_id] = Cp2kEnvironment(self, env_id)
        return self.envs[env_id]

    def chdir(self, dir):
        """Change the working directory to `dir`."""

        self.exec_cmd('cd ' + dir)

    def getcwd(self):
        """Return the working directory."""

        return self.exec_cmd('pwd')[0][:-1]


class Cp2kEnvironment:
    """ """

    def __init__(self, connection, env_id):
        """ """

        self.connection = connection
        self.env_id = env_id

    def eval_e(self):
        """Evaluate the energy in the background."""

        nerr = self.connection.nErrors
        self.connection.exec_cmd('eval_e %d\n'%(self.env_id), async=1)
        self.connection.raiseLastError(nerr)

    def eval_ef(self):
        """Evaluate the energy and forces in the background."""

        nerr = self.connection.nErrors
        self.connection.exec_cmd('eval_ef %d\n'%(self.env_id), async=1)
        self.connection.raiseLastError(nerr)

    def get_pos(self):
        """Return the positions of the atoms."""

        nerr = self.connection.nErrors
        lines=self.connection.exec_cmd('get_pos %d\n'%(self.env_id))
        self.connection.raiseLastError(nerr)
        ndim=int(lines[0])
        pos=array(map(float,(''.join(lines[1:])).split()[:ndim]))
        return reshape(pos,(ndim/3, 3))

    def get_f(self):
        """Return the forces on the atoms."""

        nerr = self.connection.nErrors
        lines = self.connection.exec_cmd('get_f %d\n'%(self.env_id))
        self.connection.raiseLastError(nerr)
        ndim = int(lines[0])
        f = array(map(float,(''.join(lines[1:])).split()[:ndim]))
        return reshape(f,(ndim/3, 3))

    def get_natom(self):
        """Return the number of atoms in the environment."""

        nerr = self.connection.nErrors
        lines = self.connection.exec_cmd('natom %d\n'%(self.env_id))
        self.connection.raiseLastError(nerr)
        return int(lines[0])

    def get_e(self):
        """Return the energy of the last configuaration evaluated,
         Return 0.0 if none was evaluated."""

        nerr = self.connection.nErrors
        lines = self.connection.exec_cmd('get_e %d\n'%(self.env_id))
        self.connection.raiseLastError(nerr)
        return float(lines[0])

    def set_pos(self, pos):
        """Change the positions of the atoms.
        Return the maximum change in coordinates."""
        nerr = self.connection.nErrors
        fin = self.connection.st.stdin
        fin.write('set_pos %d\n'%(self.env_id))
        p = ravel(pos)
        fin.write("%d\n"%(p.size))
        for pp in p:
            fin.write(' %18.13f'%(pp))
        fin.write("\n* END\n")
        fin.flush()
        lines = self.connection.getReady()
        self.connection.raiseLastError(nerr)
        return float(lines[0])

    def destroy(self):
        """Destroy this environment."""

        nerr = self.connection.nErrors
        lines = self.connection.exec_cmd('destroy %d\n'%(self.env_id))
        self.connection.envs[self.env_id]
        self.env_id = -1
        self.connection.raiseLastError(nerr)
