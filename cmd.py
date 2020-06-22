class CMD:
    """
        comm: str: pitch, yaw, height, None
        amount: int: how much to move
    """
    def __init__(self, comm:str, amount:int):
        self.cmd = None
        self.amount = None
        if comm not in ['pitch', 'yaw', 'height']:
            print('bad cmd')
            self.cmd = ''
            self.amount = 0
        self.cmd = comm
        self.amount = amount

    def __repr__(self):
        return f"{self.cmd}::{self.amount}"
