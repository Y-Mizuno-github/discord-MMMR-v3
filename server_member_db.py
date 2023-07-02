import sqlite3
from typing import Tuple

class server_table:
    def __init__(self):
        self.db_name = 'sqlite_db/server_info.sqlite'
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()
        self.curs.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="server"')

        if self.curs.fetchone()[0] == 0: # database not exist
            self.bool_db_exist = False
        else: # database exist
            self.bool_db_exist = True

        if not self.bool_db_exist:
            self.curs.execute('''CREATE TABLE server(id integer primary key, notify_channel text, dnd_channel text, dropbox_token text, admin integer)''')

    def get_metrics(self, id:int, metrics:str) -> Tuple[str, int]:
        self.curs.execute("SELECT * FROM server WHERE ID=?", (id,))
        row = self.curs.fetchall()

        if not row:
            print("entry not exist (server_table:get_metrics)")
            return None, -1

        if metrics == "notify_channel" or metrics == "dnd_channel" or metrics == "dropbox_token":
            if row[0][metrics] == None:
                return None, 1
            return row[0][metrics], 0
        else:
            print("metrics error (server_table:get_metrics)")
            return None, -2

    def set_metrics(self, id:int, metrics:str, value:str) -> int:
        self.curs.execute("SELECT * FROM server WHERE id=?", (id,))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO server (id, notify_channel, dnd_channel, dropbox_token, admin) values (?,?,?,?,?)'
            data = (id,None,None,None,0)
            self.curs.execute(sql,data)
        
        if metrics == "notify_channel":
            sql_update = "UPDATE server SET notify_channel = ? WHERE id = ?"
        elif metrics == "dnd_channel":
            sql_update = "UPDATE server SET dnd_channel = ? WHERE id = ?"
        elif metrics == "dropbox_token":
            sql_update = "UPDATE server SET dropbox_token = ? WHERE id = ?"
        else:
            print("metrics error (server_table:set_metrics)")
            return -2
        
        data = (value, id)
        self.curs.execute(sql_update,data)
        self.conn.commit()
        return 0
    
    def get_bool_admin(self, id:int) -> bool:
        self.curs.execute("SELECT * FROM server WHERE id=?", (id,))
        row = self.curs.fetchall()

        if not row:
            print("entry not exist (server_table:get_bool_admin)")
            return None, -1
        
        if row[0]["admin"] == 0 or row[0]["admin"] == 1:
            return bool(row[0]["admin"]), 0
        else:
            print("error admin is not bool (server_table:get_bool_admin)")
            return None, -2

    
    def set_bool_admin(self, id:int, bool_admin:bool) -> int:
        self.curs.execute("SELECT * FROM server WHERE id=?", (id,))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO server (id, notify_channel, dnd_channel, dropbox_token, admin) values (?,?,?,?,?)'
            data = (id,None,None,None,0)
            self.curs.execute(sql,data)
        
        sql_update = "UPDATE server SET admin = ? WHERE id = ?"
        data = (int(bool_admin), id)
        self.curs.execute(sql_update,data)
        self.conn.commit()
        return 0

    def __del__(self):
        self.conn.commit()
        self.conn.close()

class member_table:
    def __init__(self):
        self.db_name = 'sqlite_db/member_info.sqlite'
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()
        self.curs.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="member"')

        if self.curs.fetchone()[0] == 0: # database not exist
            self.bool_db_exist = False
        else: # database exist
            self.bool_db_exist = True

        if not self.bool_db_exist:
            self.curs.execute('''CREATE TABLE member(member_id integer, server_id integer, voice_tone text, voice_speed text, notify_name text, notify_on integer, admin integer, primary key(member_id, server_id))''')

    def get_metrics(self, member_id:int, server_id:int, metrics:str) -> Tuple[str, int]:
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        row = self.curs.fetchall()

        if not row:
            print("entry not exist (member_table:get_metrics)")
            return None, -1

        if metrics == "voice_tone" or metrics == "voice_speed" or metrics == "notify_name":
            if row[0][metrics] == None:
                return None, 1
            else:
                return row[0][metrics], 0
        else:
            print("metrics error (member_table:get_metrics)")
            return None, -2

    def set_metrics(self, member_id:int, server_id:int, metrics:str, value:str) -> int:
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO member (member_id, server_id, voice_tone, voice_speed, notify_name, notify_on, admin) values (?,?,?,?,?,?,?)'
            data = (member_id, server_id, None, None, None, 1, 0)
            self.curs.execute(sql,data)
        
        if metrics == "voice_tone":
            sql_update = "UPDATE member SET voice_tone = ? WHERE member_id = ? and server_id = ?"
        elif metrics == "voice_speed":
            sql_update = "UPDATE member SET voice_speed = ? WHERE member_id = ? and server_id = ?"
        elif metrics == "notify_name":
            sql_update = "UPDATE member SET notify_name = ? WHERE member_id = ? and server_id = ?"
        else:
            print("metrics error (member_table:set_metrics)")
            return -2       
        data = (value, member_id, server_id)
        self.curs.execute(sql_update,data)
        self.conn.commit()
        return 0
    
    def set_bool_notify(self, member_id:int, server_id:int, value:int) -> int:
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO member (member_id, server_id, voice_tone, voice_speed, notify_name, notify_on, admin) values (?,?,?,?,?,?,?)'
            data = (member_id, server_id, None, None, None, 1, 0)
            self.curs.execute(sql,data)
        
        sql_update = "UPDATE member SET notify_on = ? WHERE member_id = ? and server_id = ?"
        data = (value, member_id, server_id)
        self.curs.execute(sql_update,data)
        self.conn.commit()
        return 0
    
    def get_bool_notify(self, member_id:int, server_id:int) -> Tuple[bool, int]:
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        row = self.curs.fetchall()

        if not row:
            print("entry not exist (member_table:get_bool_notify)")
            return None, -1
        
        return row[0]["notify_on"], 0
    
    def get_bool_admin(self, member_id:int, server_id:int) -> Tuple[bool, int]:
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        row = self.curs.fetchall()

        if not row:
            print("entry not exist (member_table:get_bool_admin)")
            return None, -1
        
        return row[0]["admin"], 0


    def __del__(self):
        self.conn.commit()
        self.conn.close()