from cmd import CMD

class Skullpkt:
    def __init__(self):
        self.task_id = 0
        self.time_of_cmd = 0
        self.cmds = []
    
    def __repr__(self):
        return f'[{self.task_id}] @ {self.time_of_cmd} -> {self.cmds}'
    
    def add_cmd(self, cmd:CMD):
        self.cmds.append(cmd)

if __name__ == "__main__":
    sk = Skullpkt()
    print(sk)