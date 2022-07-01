import psycopg2
import psycopg2.extras
import logging
class PostgresManager(object):
    def __init__(self):
        self.conn = None
        self.cursor = None
    #end
    
    def connect2(self, host, database="tenis", user="tenis", password="2sfcNavA89A294V4"):
        if self.conn == None:
            try:
                self.conn = psycopg2.connect(host=host, database=database, user=user, password=password)
                self.conn.autocommit = True #transaction i otomatik commitleyerek hata olsa dahi devam edebilmeyi sağlar.
                self.cursor = self.conn.cursor()
                logging.info("PostgreSQL Bağlantısı Kuruldu!")
                return "PostgreSQL Bağlantısı Kuruldu!"
            except Exception as e:
                logging.info(f"PostgreSQL Bir Sorunla Karşılaşıldı: {e}")
                return f"PostgreSQL Bir Sorunla Karşılaşıldı: {e}"
        return "Postgres Zaten Bağlı"
    #end        

    def disconnect(self):
        #Bağlantıyı keser
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logging.info("PostgreSQL Bağlantısı Kesildi!")
            self.conn = None
            self.cursor = None
    #end

    #*QUERY----------------------------------------------------------------------------------------
    def executeSelectQuery(self, query):
        values = None
        self.cursor.execute(query)
        values = self.cursor.fetchall()
        return values
    #end

    #*INSERT---------------------------------------------------------------------------------------
    def executeCommitQuery(self, query, values):
        """
        example:
            query = INSERT INTO table(A,B,C) VALUES (%s,%s,%s);
            values = [1,2,3]
        """
        self.cursor.execute(query, values)
        res = self.conn.commit()
        return res
    #end
   
    def insert(self, tableName, columns=[], values=[]):
        #Dynamic insert
        sss = ""
        for i in range(len(columns)):
            sss = sss + '%s,'
        sss = sss[:-1]
        
        columnsStr = ""
        for x in columns:
            columnsStr = columnsStr + x + ','
        columnsStr = columnsStr[:-1]
        
        query = """INSERT INTO {}({}) VALUES ({});""".format(tableName, columnsStr, sss)
        self.cursor.execute(query, values)
        self.conn.commit()
    #end

    def batchInsert(self, curs, query, values):
        #values = [(insertArray[0][0], insertArray[0][1], 2, 'Maskesiz', insertArray[0][6] ,False)]
        psycopg2.extras.execute_batch(curs, query, values)
        self.conn.commit()
    #end

#end::class


if __name__ == "__main__":
    db = PostgresManager()
    db.connect2()
    list = db.executeSelectQuery('''SELECT * FROM public."Player" ''')
    logging.info(list)
    db.disconnect()
    #val = db.select()
    #logging.info(val)