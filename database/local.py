db_params = {
    'host': 'localhost',
    'dbname': 'quitter_db',
    'user': 'postgres',
    'password': 'your_password',
}

db_params_sa = db_params.copy()
db_params_sa['database'] = db_params_sa.pop('dbname')
db_params_sa['username'] = db_params_sa.pop('user')