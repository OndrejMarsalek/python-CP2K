import cp2k

cp2k.sbp.verbose = True

print 'create connection'
connection = cp2k.Connection(host='localhost', port=4329)

print 'create Ar env'
env_Ar = connection.create_env('Ar.inp')
