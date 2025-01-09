import sys
def sizeof(obj):
    size = sys.getsizeof(obj)
    if isinstance(obj, dict): return size + sum(map(sizeof, obj.keys())) + sum(map(sizeof, obj.values()))
    if isinstance(obj, (list, tuple, set, frozenset)): return size + sum(map(sizeof, obj))
    return size


class MessageHistory:
    def __init__(self):
        self.__history = []
        self.__num_received = 0
        self.__num_sent = 0
        self.__bytes_sent = 0
        self.__bytes_received = 0

    def add_message(self, message, destination):
        self.__history.append((destination, message))
        self.__num_sent += 1
        # print(f"Message sent to {destination}: {sizeof(message)}")
        self.__bytes_sent += sizeof(message)
    
    def receieve_message(self):
        self.__num_received += 1

    def get_history(self):
        return self.__history

    def clear_history(self):
        self.__history = []
    
    def __len__(self):
        return len(self.__history)
    
    def bytes_sent(self):
        return self.__bytes_sent