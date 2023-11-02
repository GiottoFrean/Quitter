db_params = {
    'host': 'localhost',
    'dbname': 'database_name_goes_here',
    'user': 'postgres',
    'password': 'password_goes_here',
}

db_params_sa = db_params.copy()
db_params_sa['database'] = db_params_sa.pop('dbname')
db_params_sa['username'] = db_params_sa.pop('user')