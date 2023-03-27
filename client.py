import threading
import socket
import json
from cmd import Cmd

def login_required(func):
    """
    Decorator: need to login first
    """
    def inner(*args, **kwargs):
        if args[0].get_login_status():
            return func(*args, **kwargs)
        else:
            print('Please login first')
    return inner

class Client(Cmd):
    """
    客户端
    """
    prompt = ''
    intro = '[Welcome] 简易聊天室客户端(Cli版)\n' + '[Welcome] 输入help来获取帮助\n'

    def __init__(self, ip: str, port:int) -> None:
        """
        构造
        """
        super().__init__()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__id = None
        self.__user = None
        self.__isLogin = False
        self.server_address = (ip, port)

    def get_login_status(self):
        return self.__isLogin

    def __handle_system_message(self, obj):
        try:
            type = obj['type']
            message = obj['message']
            if obj['type'] == 'online':
                for key, value in message.items():
                    print("User Id:", key, ',', "Nickname:", value)
            elif obj['type'] == 'error':
                print(obj['message'])
            elif obj['type'] == 'connection_check':
                pass
        except Exception:
            print('[Client] 解析系统消息失败')

    def __receive_message_thread(self):
        """
        接受消息线程
        """
        while self.__isLogin:
            # noinspection PyBroadException
            try:
                buffer = self.__socket.recv(1024).decode()
                obj = json.loads(buffer)
                if obj['sender_id'] == 0:
                    self.__handle_system_message(obj)
                else:
                    print('[' + str(obj['sender_id']) + '(' + str(obj['sender_nickname']) + ')' + ']', obj['message'])
            except Exception:
                print('[Client] 无法从服务器获取数据')

    def __send_message_thread(self, receiver_id, message):
        """
        发送消息线程
        :param message: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'chat',
            'sender_id': f'{self.__id}',
            'receiver_id': f'{receiver_id}',
            'message': message
        }).encode())

    def start(self):
        """
        启动客户端
        """
        self.__socket.connect(self.server_address)
        self.cmdloop()

    def do_login(self, args):
        """
        登录聊天室
        :param args: 参数
        """
        user = args.split(' ')[0]

        if len(user) > 0:
        # 将昵称发送给服务器，获取用户id
            self.__socket.send(json.dumps({
                'type': 'login',
                'user': user
            }).encode())
            # 尝试接受数据
            # noinspection PyBroadException
            try:
                buffer = self.__socket.recv(1024).decode()
                obj = json.loads(buffer)
                if obj['id']:
                    self.__user = user
                    self.__id = obj['id']
                    self.__isLogin = True
                    print('[Client] 成功登录到聊天室')

                    # 开启子线程用于接受数据
                    thread = threading.Thread(target=self.__receive_message_thread)
                    thread.setDaemon(True)
                    thread.start()
                else:
                    print('[Client] 无法登录到聊天室')
            except Exception:
                print('[Client] 无法从服务器获取数据')
        else:
            print('Invalid nickname')

    @login_required
    def do_send(self, args:str) -> None:
        """
        发送消息
        :param args: 参数
        """
        receiver_id, message = args.split(' ', 1)
        # 显示自己发送的消息
        print('[' + str(self.__user) + ']' + 'to',receiver_id, ':', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__send_message_thread, args=(receiver_id, message,))
        thread.setDaemon(True)
        thread.start()

    @login_required
    def do_logout(self, args=None):
        """
        登出
        :param args: 参数
        """
        self.__socket.send(json.dumps({
            'type': 'logout'}).encode())
        self.__isLogin = False
        return True
    
    @login_required
    def do_online(self, args=None):
        """
        查询在线用户
        :param args: 参数
        """
        self.__socket.send(json.dumps({
            'type': 'online'
        }).encode())

    def do_help(self, arg=None):
        print('[Help] login user - 登录，user是你选择的昵称')
        print('[Help] online - 查询在线用户')
        print('[Help] send user_id message - 发送消息，user_id是用户id, message是你输入的消息')
        print('[Help] logout - 退出')

