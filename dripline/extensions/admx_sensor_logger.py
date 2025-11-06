'''
Dan Zhang  migrate DL2 to DL3 multi format entity to send multiple commands at once
'''

import sqlalchemy
from dripline.implementations.postgres_sensor_logger import PostgresSensorLogger 
from dripline.implementations.postgres_interface import SQLTable
import logging
import scarab
import numpy as np
logger = logging.getLogger(__name__)

__all__ = ['ADMXSensorLogger']



class ADMXSensorLogger(PostgresSensorLogger):
    '''In standard SCPI, you should be able to send a bunch of requests separated by colons
       This spime does this and returns a json structure organized by label'''
    def __init__(self,
                 sensor_type_map_table="",
                 sensor_type_match_column="sensor_name",
                 sensor_type_column_name="epics_data_type",
                 data_tables_dict={},
                 **kwargs):
        '''
        sensor_type_map_table (str): name of the child endpoint of this instance which provides access to the endpoint_id_map, which stores the sensor type
        sensor_type_column_name (str):  name of the column to use for the return type (matched against keys in the data_tables_dict argument here)
        sensor_type_match_column (str): column against which to check for matches to the sensor name
        data_tables_dict (dict):  dictionary mapping types (in the sensor_type_map_table) to child endpoints of this instance which provide access to the data_table for that type
        '''
        PostgresSensorLogger.__init__(self, **kwargs)
        self._sensor_type_map_table=sensor_type_map_table
        self._sensor_type_match_column = sensor_type_match_column
        self._sensor_type_column_name = sensor_type_column_name
        self._data_tables_dict = data_tables_dict
   

    def process_payload(self, a_payload, a_routing_key_data, a_message_timestamp):
        
        try:
            sensor_name = a_routing_key_data["sensor_name"]
            this_type = None
            this_table = self.sync_children[self._sensor_type_map_table]
            where_eq_dict_local ={self._sensor_type_match_column: sensor_name}
            column_name = self._sensor_type_column_name
            this_type = this_table.do_select(return_cols=[column_name], where_eq_dict=where_eq_dict_local)
            logger.debug(f"{this_type}")
            if not this_type[1]:
                logger.critical('endpoint with name "{}" was not found in database hence failed to log its value; might need to add it to the db'.format(sensor_name))
                return
            else:
                sensor_type = this_type[1][0][0]
                if not sensor_type in self._data_tables_dict:
                    logger.critical(f'endpoint with name "{sensor_name}" is not configured with a recognized type in the sensors_list table')
                    logger.critical(f'sensor type is {sensor_type}')
                    logger.critical(f'data tables: {self._data_tables_dict}')
                    return
                else:
                    this_data_table = self.sync_children[self._data_tables_dict[sensor_type]]

                    # combine data sources
                    insert_data = {'timestamp': a_message_timestamp}
                    insert_data.update(a_routing_key_data)
                    insert_data.update(a_payload.to_python())
                    logger.info(f"Inserting from endpoint {self._data_tables_dict[sensor_type]}; data are:\n{insert_data}")
                    # do the insert
                    insert_return = this_data_table.do_insert(**insert_data)
                    logger.debug(f"Return from insertion: {insert_return}")
                    logger.info("finished processing data")
        except sqlalchemy.exc.SQLAlchemyError as err:
            logger.critical(f'Received SQL error while doing insert: {err}')
        except Exception as err:
            logger.critical(f'An exception was raised while processing a payload to insert: {err}')

__all__.append("ADMXSpecLogger")
class ADMXSpecLogger(ADMXSensorLogger):
    '''
    write to two tables for a admx digitization
    data_tables_dict is supposed to point to more than one table
    '''
    def __init__(self, **kwargs):
        ADMXSensorLogger.__init__(self,**kwargs)



    def process_payload(self, a_payload, a_routing_key_data, a_message_timestamp):

        try:
            sensor_name = a_routing_key_data["sensor_name"]
            this_type = None
            this_table = self.sync_children[self._sensor_type_map_table]
            where_eq_dict_local ={self._sensor_type_match_column: sensor_name}
            column_name = self._sensor_type_column_name
            this_type = this_table.do_select(return_cols=[column_name], where_eq_dict=where_eq_dict_local)
            logger.debug(f"{this_type}")
            if not this_type[1]:
                logger.critical('endpoint with name "{}" was not found in database hence failed to log its value; might need to add it to the db'.format(sensor_name))
                return
            else:
                sensor_type = this_type[1][0][0]
                if not sensor_type in self._data_tables_dict:
                    logger.critical(f'endpoint with name "{sensor_name}" is not configured with a recognized type in the sensors_list table')
                    logger.critical(f'sensor type is {sensor_type}')
                    logger.critical(f'data tables: {self._data_tables_dict}')
                    return
                else:
                    the_spec = np.array(a_payload.to_python()["value_raw"],dtype=float)
                    for table_name_i in self._data_tables_dict[sensor_type]:
                        this_data_table = self.sync_children[table_name_i]
                        insert_data = {'timestamp': a_message_timestamp}
                        if not (this_data_table._bool_calculation):
                            # combine data sources
                            convert_the_spec = [ float(i) for i in the_spec ]
                            insert_data.update(a_routing_key_data)
                            insert_data.update(a_payload.to_python())
                            insert_data.update({"value_raw": convert_the_spec})
                            
                            logger.info(f"Inserting from endpoint {table_name_i}; data test:\n{insert_data['value_raw'][0]}")
                            # do the insert
                            insert_return = this_data_table.do_insert(**insert_data)
                            logger.debug(f"Return from insertion: {insert_return}")
                        else:
                            this_mean = float(np.mean(the_spec))
                            this_std = float(np.std(the_spec))
                            insert_data.update({"sensor_name": this_data_table._sensor_name_mean,
                                                "raw_value": this_mean, "calibrated_value":this_mean})
                            logger.info(f"Inserting from endpoint {table_name_i}; data test:\n{insert_data}")
                            insert_return = this_data_table.do_insert(**insert_data)
                            logger.debug(f"Return from insertion mean: {insert_return}")
                            insert_data.update({"sensor_name": this_data_table._sensor_name_std,
                                                "raw_value": this_std, "calibrated_value":this_std})
                            logger.info(f"Inserting from endpoint {table_name_i}; data test:\n{insert_data}")
                            insert_return = this_data_table.do_insert(**insert_data)
                            logger.debug(f"Return from insertion std: {insert_return}")
                    logger.info("finished processing data")


        except sqlalchemy.exc.SQLAlchemyError as err:
            logger.critical(f'Received SQL error while doing insert: {err}')
        except Exception as err:
            logger.critical(f'An exception was raised while processing a payload to insert: {err}')




__all__.append("ADMXSQLTable")
class ADMXSQLTable(SQLTable):
    '''
    rewrite the on_get of SQLTable
    '''
    def __init__(self, *args, **kwargs):
        SQLTable.__init__(self, *args, **kwargs)

    def get_action(self):
        this_table = self.table_name
        this_column = self.service._sensor_type_match_column
        return_cols = [this_column]
        this_select = sqlalchemy.select(*[getattr(self.table.c,col) for col in return_cols]).order_by(this_column).fetch(1)
        conn = self.service.engine.connect()
        result = conn.execute(this_select)
        conn.commit()
        list_result = [i for i in result]

        return list_result

    def on_get(self):

        N_trial = 1
        for i in range(N_trial):
          list_result = self.get_action()
          if len(list_result[0])>0: break
          else:
            logger.critical(f'try on_get fail {i}, try reconnect to the database')
            self.service.connect_to_db(self.service.auth)
            list_result = self.get_action()

        result = list_result[0][0]
        logger.info(f'SQL object get {result}')
        return result



__all__.append("ADMXSpecSQLTable")
class ADMXSpecSQLTable(SQLTable):
    '''
    rewrite the on_get of SQLTable
    '''
    def __init__(self,
                  bool_calculation = False,
                  sensor_name_mean = "",
                  sensor_name_std = "",
                  *args, **kwargs):
        '''
        sensor_name_mean (string): name of the sensor to log with the mean of the spectrum
        sensor_name_std (string): name of the sensor to log with the STD of the spectrum
        do_upsert (bool): indicates if conflicting inserts should then update
        '''
        self._bool_calculation = bool_calculation
        self._sensor_name_mean = sensor_name_mean
        self._sensor_name_std = sensor_name_std
        SQLTable.__init__(self, *args, **kwargs)
