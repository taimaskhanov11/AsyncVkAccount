import peewee as pw

db = pw.MySQLDatabase('test_db', user='root', password='root',
                      host='localhost', port=3306)


class BaseModel(pw.Model):
    """A base model that will use our Postgresql database"""

    class Meta:
        database = db


class User(BaseModel):
    username = pw.CharField()



if __name__ == '__main__':
    db.create_tables([User])
