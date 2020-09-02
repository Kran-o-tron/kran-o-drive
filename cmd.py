cmds = ['pitch', 'yaw', 'height', 'roll', 'width', 'save', 'load', 'list', 'reset', 'close',
        'playback']

class CMD:
    """
        comm: str: pitch, yaw, height, None
        amount: int: how much to move
    """

    def __init__(self, comm: str, amount: int = None, pos: dict = None): 
        self.action = None
        self.amount = amount
        if comm not in cmds:
            print('bad cmd')
            self.action = ''
            self.amount = 0
        self.action = comm
        self.amount = amount
        self.pos = pos

    def __repr__(self):
        return f"{self.action}::{self.amount}"

    def get_action(self) -> str:
        return self.action

    def get_amount(self) -> int:
        return self.amount

    @staticmethod
    def permitted_cmds():
        return cmds
