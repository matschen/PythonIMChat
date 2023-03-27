class User:
    def __init__(self, id, nickname, connection):
        self.__id = id
        self.__nickname = nickname
        self.__connection = connection
    
    @property
    def id(self):
        return self.__id
    
    @property
    def nickname(self):
        return self.__nickname
    
    @property
    def connection(self):
        return self.__connection
    

    