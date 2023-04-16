import psycopg2
from db_operation_functions import queryComposer
import pandas as pd
import numpy as np

password = input("Пароль от админа postgres: ")

conn = psycopg2.connect(
    host="localhost", database="postgres", user="postgres", password=password, port=5432
)
conn.set_session(autocommit=True)
username = "of_user"
password_n = "0000"
db_name = "oil_factory_db"

cur = conn.cursor()
cur.execute(f"CREATE USER {username} WITH PASSWORD '{password_n}';")
cur.execute(f"ALTER USER {username} CREATEDB;")
cur.close()

cur = conn.cursor()
cur.execute(f"CREATE DATABASE {db_name} OWNER {username};")
cur.close()

cur = conn.cursor()
cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username};")
cur.close()
conn.close()

conn = psycopg2.connect(
    host="localhost", database=db_name, user=username, password=password_n, port=5432
)
conn.set_session(autocommit=True)

cur = conn.cursor()
with open("sql_qq.sql", "r", encoding="utf-16") as f:
    sql = f.read()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()

# import data new

df = pd.read_csv("risk_register_final.csv")
df.drop(columns=["Unnamed: 0"], inplace=True)

conn = psycopg2.connect(
    host="localhost", database=db_name, user=username, password=password_n, port=5432
)
cur = conn.cursor()
query = """
insert into risk_classification(risk_class_name)
values 
    ('Риски персонала'),
    ('Финансовые риски'),
    ('Технологические риски'),
    ('Юридические риски'),
    ('Экологичесике риски'),
    ('Эксплуатационные риски'),
    ('Стратегические риски'),
    ('Форс-мажорные риски');
"""
cur.execute(query)
conn.commit()
cur.close()
conn.close()


conn_params = {
    "host": "localhost",
    "database": db_name,
    "user": username,
    "password": password_n,
    "port": 5432,
}

qc = queryComposer("risk_register", conn_params=conn_params)
for idx, rec in df.iterrows():
    tmp = dict(rec)
    qc.insert_query(tmp)
qc.close_connection()

pm_df = pd.read_csv("pm_df_data.csv")
pm_df.drop(columns=["Unnamed: 0"], inplace=True)
pm_df.columns = ["risk_id", "prevention_measure_name"]


qc = queryComposer("prevention_measures", conn_params=conn_params)
for _, rec in pm_df.iterrows():
    try:
        qc.insert_query(dict(rec))
    except:
        print("oshibqa")
qc.close_connection()


conn = psycopg2.connect(
    host="localhost", database=db_name, user=username, password=password_n, port=5432
)
conn.set_session(autocommit=True)

cur = conn.cursor()
query = """insert into sensor_type(sensor_type_name)
 values 
	('Датчик давления'),
	('Датчик силы'),
	('Датчик момента'),
	('Датчик загазованности'),
	('Датчик температуры'),
	('Датчик уровня'),
	('Датчик плоности');"""
cur.execute(query)

query = """insert into sensor_unit(unit_name, sensor_type_id)
values 
	('Мпа', 1),
	('кгс', 2),
	('кН м', 3),
	('мг/м3', 4),
	('градус Цельсия', 5),
	('м', 6),
	('г/см3', 7);
    """
cur.execute(query)

query = """
insert into equipment_type(equipment_type_name, equipment_type_details)
values
	('Сепаратор НГС вертикальный','вертикальный'),
	('Фильтр низкого давления для сжиженого газа','низкое'),
	('Полупроходной газовый кран','полупроходной'),
	('Факельный столб','часть факельной установки'),
	('Лопостной насос','газовый'),
	('Динамический компрессор','газовый'),
	('Ретификационная коллона','нефтяная'),
	('Резервуар горизонтальный стальной РГС','газовый');
"""
cur.execute(query)
query = """
insert into equipment(equipment_name, equipment_designation, equipment_type_id,  equipment_installation_date, equipment_average_lifetime, equipment_status)
values
    ('Сепаратор природного газа','LvIL-XVd~RJBT/WC',1,'2020-01-28',6,true),
	('Резервуар горизонтальный стальной РГС 63 м3' ,'oApoM.vqj.XgUP_EJ' ,8 ,'2020-01-10', 10, true ),
	('НАСОС ДЛЯ ГАЗА ПРОПАН HYDRO VACUUM' ,'IvYOT~Csd~Nj' ,5,'2020-01-05', 8, true ),
	('Ретификационная коллона NalsdbKuasdn' ,'OfXfE.WMtx.eC' ,7 ,'2020-01-07', 6 , true);
"""
cur.execute(query)
#
query = """insert into sensor(sensor_name, sensor_type_id, unit_id, limit_mode_value, equipment_id)
values 
	('Датчик силы ИВЭ-50-2',2 ,2 , 20000, 1),
	('Датчик силы ИВЭ-50-2',2 ,2 , 20000, 2),
	('Датчик давления ИВЭ-50-3', 1, 1, 2, 1),
	('Датчик давления ИВЭ-50-3', 1, 1, 2, 2),
	('Устройство измерения давления ИВЭ-50ИД', 1, 1, 25, 1),
	('Устройство измерения давления ИВЭ-50ИД', 1, 1, 40, 2),
	('Датчик ИВЭ-50-2.9', 3, 3, 6250, 1),
	('Датчик момента ключа ГКШ-МТ', 3, 3, 6250, 1),
	('Автономный мобильный газоанализатор ИВЭ-50-4.6',4 ,4 ,100, 2 ),
	('Датчик уровня ИВЭ-50-5М',6 ,6 ,5 , 3),
	('Датчик плотности ДПЛ-3',7 ,7 ,3 , 4),
	('Датчик температуры ИВЭ-50-6',5 ,5 ,100 , 1),
	('Датчик температуры ИВЭ-50-6',5 ,5 ,100 , 2),
	('Датчик температуры ИВЭ-50-6',5 ,5 ,100 , 3),
	('Датчик температуры ИВЭ-50-6',5 ,5 ,100 , 4);
	"""
cur.execute(query)

cur.close()
conn.close()
