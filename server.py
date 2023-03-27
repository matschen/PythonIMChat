import threading
import socket
import json
from user import User
import time

def is_online(func):
    """
    Decorator: check if user is online
    """
    def inner(*args, **kwargs):
        if args[2] in args[0].users:
            func(*args, **kwargs)
        else:
            args[0].users[args[1]].connection.send(json.dumps({
                    'sender_id': 0,
                    'sender_nickname': 'System',
                    'type': 'error',
                    'message':'User does not exist'
                }).encode()
            )
    return inner

class Server:
    
    def __init__(self, ip: str, port: int) -> None:
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = {}   # 存放User类对象的列表，表示在线用户
        self.address = (ip, port)
    
    def __check_connection_status(self):
        while True:
            for key, user in self.users.items():
                try:
                    self.__send_system_message(user.connection, 'connection_check')
                except Exception:
                    del self.users[key]
            time.sleep(5)

    def get_online_user(self) -> dict:
        try:
            dict = {}
            for _, user in self.users.items():
                dict[user.id] = user.nickname
            return dict
        except Exception:
            print("[Server] 尝试获取在线用户失败")
    
    def __user_thread(self, user: User):
        """
        用户子线程
        :param user_id: 用户id  
        """
        print("[Server] 用户", user.nickname, '登录了')

        while True:
            try:
                buffer = user.connection.recv(1024).decode()
                obj = json.loads(buffer)
                if obj['type'] == 'chat':
                    self.__send_message(obj['sender_id'], obj['receiver_id'], obj['message'])
                elif obj['type'] == 'online':
                    print(f"User {user.nickname} query online users")
                    type = 'online'
                    self.__send_system_message(user.connection, type, self.get_online_user())
                elif obj['type'] == 'logout':
                    print(f'User {user.nickname} logout')
                    del self.users[f'{user.id}']
            except Exception:
                print('[Server] 连接失效:', user.connection.getsockname(), user.connection.fileno())
                del self.users[f'{user.id}']
                break

    def __send_system_message(self, connection, type='', message=''):
        '''
        服务器发送系统通知
        '''
        connection.send(json.dumps({
            'sender_id': 0,
            'sender_nickname': 'System',
            'type': type,
            'message': message
        }).encode())


    @is_online
    def __send_message(self, sender_id: str, receiver_id: str, message=''):
        """
        :param sender_id: 发送者id
        :param receiver_id: 接收者id
        :param message: 消息内容
        """
        self.users[receiver_id].connection.send(json.dumps({
            'sender_id': sender_id,
            'sender_nickname': self.users[sender_id].nickname,
            'message': message
        }).encode())

            
    def __waitForLogin(self, connection):
        try:
            buffer = connection.recv(1024).decode()
            # 解析成json数据
            obj = json.loads(buffer)
            # 如果是连接指令，那么则返回一个新的用户编号，接收用户连接
            if obj['type'] == 'login':
                user = User(connection.fileno(), obj['user'], connection)
                self.users[f'{connection.fileno()}'] = user
                connection.send(json.dumps({
                    'id': user.id
                }).encode())
                # 开辟一个新的线程处理消息
                thread = threading.Thread(target=self.__user_thread, args=(user,))
                thread.setDaemon(True)
                thread.start()
            else:
                print('[Server] 无法解析json数据包:', connection.getsockname())
        except Exception:
            print('无法接受数据',connection.getsockname())

    def start(self):
        self.__socket.bind(self.address)
        self.__socket.listen(10)
        print("Server start......")

        while True:
            connection, address = self.__socket.accept()
            print("A new connection", connection.getsockname(), address)

            thread = threading.Thread(target=self.__waitForLogin, args=(connection,))
            # setDaemon设置为True，服务器主循环停止，其他线程也就停止
            thread.setDaemon = True
            thread.start()
