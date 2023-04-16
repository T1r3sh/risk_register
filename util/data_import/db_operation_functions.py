import psycopg2
from string import Template

DEFAULT_CONNECTION_PARAMS = {
    "dbname": "oil_factory_db",
    "user": "of_user",
    "password": "0000",
    "host": "localhost",
}
# DEFAULT_CONN = psycopg2.connect(
#     dbname="oil_factory_db", user="postgres", password="9028", host="localhost"
# )


class autoQuotePlacer:
    def __init__(self, schema_info: dict) -> None:
        self.schema = schema_info

    def factor(self, values):
        res_values = {}
        for key, value in values.items():
            if value is None:
                continue
            tmp_val = str(value)
            if self.schema[key] not in [
                "integer",
                "double precision",
                "real",
                "boolean",
            ]:
                tmp_val = f"'{tmp_val}'"
            res_values[key] = tmp_val
        return res_values


class queryComposer:
    """
    Дополнительный класс инициализирующий подключение к базе данных и упрощающий запросы
    """

    def __init__(self, table_name: str, conn_params: dict = None) -> None:
        if conn_params is None:
            conn_params = DEFAULT_CONNECTION_PARAMS
        self.conn = psycopg2.connect(**conn_params)
        self.table_name = table_name
        try:
            info_query = (
                "select column_name, data_type "
                "from information_schema.columns "
                f"where table_schema='public' and table_name = '{table_name}'"
            )
            cursor = self.conn.cursor()
            cursor.execute(info_query)
            self.schema = {key: val for key, val in cursor.fetchall()}
            cursor.close()
            self.data_prep = autoQuotePlacer(self.schema)
        except (psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
            print(f"Error: {str(e)}")
            raise

    @staticmethod
    def table_fields(column_list: list[str]):
        """
        Статический метод создающий шаблоны для составления insert запросов

        :param column_list: Список колонок
        :type column_list: list[str]
        :return: первая строка с навзаниями колонок, вторая с идентичным шаблоном
        :rtype: tuple(str, str)
        """
        insert_string = value_string = "("
        for column in column_list:
            value_string += f"${column}, "
            insert_string += f"{column}, "
        value_string = value_string[:-2] + ")"
        insert_string = insert_string[:-2] + ")"
        return insert_string, value_string

    def insert_query(self, kwargs):
        """Запрос вставки

        :param kwargs: Словарь с параметрами запроса
        :type kwargs: dict of str: str
        """
        processed_data = self.data_prep.factor(kwargs)
        cursor = self.conn.cursor()
        insert_string, value_string = self.table_fields(processed_data.keys())
        value_template = Template(value_string)
        query = (
            f"insert into {self.table_name}{insert_string} "
            f"values {value_template.substitute(processed_data)};"
        )
        try:
            cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            # логирование ошибки
            print(f"Ошибка в запросе на вставку: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def delete_query(self, key, value):
        """
        Запрос на удаление

        :param key: Название ключа по которому производится удаление
        :type key: str
        :param value: Значение ключа
        :type value: int
        """
        cursor = self.conn.cursor()
        query = f"delete from {self.table_name} " f"where "
        query += f"{key}={value} ;"
        try:
            cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            # логирование ошибки
            print(f"Ошибка в запросе на удаление: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def update_query(self, kwargs):
        """
        Запрос на обновление

        :param kwargs: Словарь с параметрами запроса
        :type kwargs: dict of str: str
        """
        processed_data = self.data_prep.factor(kwargs)
        cursor = self.conn.cursor()
        query = f"update {self.table_name} set "
        while processed_data:
            key, value = processed_data.popitem()
            if not processed_data:
                query = query[:-2] + f" where {key}={value};"
                break
            query += f"{key}={value}, "
        try:
            cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            # логирование ошибки
            print(f"Ошибка в запросе на обновление: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def select_query(
        self,
        columns: list[str] = None,
        conditions: list[dict] = None,
        order_opt: list[str] = None,
    ):
        """
        Запрос на выборку

        :param conditions: список словарей с условиями, defaults to None
        :type conditions: dict, optional
        :return: словарь содержащий результат запроса
        :rtype: dict of str:str
        """
        cursor = self.conn.cursor()
        if columns is None:
            qcolumn = "*"
        else:
            qcolumn = ""
            for column in columns:
                qcolumn += column + ", "
            qcolumn = qcolumn[:-2]
        query = f"select {qcolumn} from {self.table_name} "
        if conditions is not None:
            cond_query = "where "
            while conditions:
                tmp_cond = conditions.pop()
                cond_query += f"{tmp_cond['key_name']} {tmp_cond['comp_operand']} {tmp_cond['key_value']}"
                if conditions:
                    cond_query += " and "
            query += cond_query
        if order_opt is None:
            query += " order by 1;"
        else:
            query += " order by "
            for opt in order_opt:
                query += f"{opt}, "
            query = query[:-2] + ";"
        cursor.execute(query)
        raw_data = cursor.fetchall()
        cursor.close()
        data = []
        for elem in raw_data:
            tmp_data = {}
            for idx, (key, instance) in enumerate(self.schema.items()):
                if elem[idx] is None:
                    tmp_data[key] = None
                    continue
                if instance in ["text", "character"]:
                    tmp_data[key] = elem[idx].strip()
                    continue
                tmp_data[key] = elem[idx]
            data.append(tmp_data)
        return data

    def close_connection(self):
        """_summary_"""
        self.conn.close()


if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname="oil_factory_db", user="postgres", password="9028", host="localhost"
    )
    qc = queryComposer("equipment")
    cond = [
        {"key_name": "equipment_status", "comp_operand": "=", "key_value": "False"},
        {"key_name": "equipment_type_id", "comp_operand": "=", "key_value": "2"},
    ]
    data = qc.select_query(
        conditions=cond, order_opt=["equipment_status", "equipment_id"]
    )
    print(data)
    # data = get_risk_list(conn)
    # print(data)
    conn.close()
