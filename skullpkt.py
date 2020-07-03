from cmd import CMD

class Skullpkt:
    def __init__(self, height:int=None, pitch:int=None, yaw:int=None):
        self.task_id = 0
        self.time_of_cmd = 0
        self.cmds = []
        
        """ for save command """
        self.height = height
        self.pitch = pitch
        self.yaw = yaw
    
    def __repr__(self):
        return f'[{self.task_id}] @ {self.time_of_cmd} -> {self.cmds}'
    
    def add_cmd(self, cmd:CMD):
        self.cmds.append(cmd)
    
    def get_pkt_cmds(self):
        return self.cmds

if __name__ == "__main__":
    sk = Skullpkt()
    print(sk)