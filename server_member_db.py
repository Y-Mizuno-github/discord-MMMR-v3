import sqlite3

class server_table:
    def __init__(self):
        self.db_name = 'server_info.sqlite'
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()
        self.curs.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="server"')

        if self.curs.fetchone()[0] == 0: # database not exist
            self.bool_db_exist = False
        else: # database exist
            self.bool_db_exist = True

        if not self.bool_db_exist:
            self.curs.execute('''CREATE TABLE server(id integer primary key, notify_channel text, dnd_channel text, dropbox_token text, admin text)''')

    def get_metrics(self, id:int, metrics:str) -> tuple(str, int):
        self.curs.execute("SELECT * FROM server WHERE ID=?", (id,))
        row = self.curs.fetchall()

        if not row:
            print("Error (get_metrics: key error)")
            return (None, -1)

        if metrics == "notify_channel" or metrics == "dnd_channel" or metrics == "dropbox_token":
            return (row[0][metrics], 0)
        else:
            print("Error (get_metrics: metrics error)")
            return (None, -2)

    def set_metrics(self, id:int, metrics:str, value:str):
        self.curs.execute("SELECT * FROM server WHERE id=?", (id,))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO server (id, notify_channel, dnd_channel, dropbox_token, admin) values (?,?,?,?,?)'
            data = (id, "0", "0", "0", "0")
            self.curs.execute(sql,data)
        
        if metrics == "notify_channel":
            sql_update = "UPDATE server SET notify_channel = ? WHERE id = ?"
        elif metrics == "dnd_channel":
            sql_update = "UPDATE server SET dnd_channel = ? WHERE id = ?"
        elif metrics == "dropbox_token":
            sql_update = "UPDATE server SET dropbox_token = ? WHERE id = ?"
        else:
            print("Error (set_metrics: metrics error)")
            return -2
        
        data = (value, id)
        self.curs.execute(sql_update,data)
        return 0

    def __del__(self):
        self.conn.commit()
        self.conn.close()

class member_table:
    def __init__(self):
        self.db_name = 'member_info.sqlite'
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()
        self.curs.execute('SELECT COUNT(*) FROM sqlite_master WHERE TYPE="table" AND NAME="member"')

        if self.curs.fetchone()[0] == 0: # database not exist
            self.bool_db_exist = False
        else: # database exist
            self.bool_db_exist = True

        if not self.bool_db_exist:
            self.curs.execute('''CREATE TABLE member(member_id integer, server_id integer, voice_tone str, voice_speed str, notify_name str, DND bool, admin bool, primary key(member_id, server_id))''')

    def get_metrics(self, member_id:int, server_id:int, metrics:str) -> tuple(str, int):
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        row = self.curs.fetchall()

        if not row:
            print("Error (get_metrics: key error)")
            return (None, -1)

        if metrics == "voice_tone" or metrics == "voice_speed" or metrics == "notify_name":
            return (row[0][metrics], 0)
        else:
            print("Error (get_metrics: metrics error)")
            return (None, -2)

    def set_metrics(self, member_id:int, server_id:int, metrics:str, value:str):
        self.curs.execute("SELECT * FROM member WHERE member_id = ? and server_id = ?", (member_id, server_id))
        if self.curs.fetchone() == None: # entry is not exist
            sql = 'INSERT INTO member (member_id, server_id, voice_tone, voice_speed, notify_name, DND, admin) values (?,?,?,?,?,?,?)'
            data = (member_id, server_id, "0", "0", "0", 0, 0)
            self.curs.execute(sql,data)
        
        if metrics == "voice_tone":
            sql_update = "UPDATE member SET voice_tone = ? WHERE member_id = ? and server_id = ?"
        elif metrics == "voice_speed":
            sql_update = "UPDATE member SET voice_speed = ? WHERE member_id = ? and server_id = ?"
        elif metrics == "notify_name":
            sql_update = "UPDATE member SET notify_name = ? WHERE member_id = ? and server_id = ?"
        else:
            print("Error (set_metrics: metrics error)")
            return -2       
        data = (value, member_id, server_id)
        self.curs.execute(sql_update,data)
        return 0

    def __del__(self):
        self.conn.commit()
        self.conn.close()