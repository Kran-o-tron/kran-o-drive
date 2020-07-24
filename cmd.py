cmds = ['pitch', 'yaw', 'height', 'roll', 'width' 'save', 'load' 'list', 'reset', 'close']

# todo implement close & reset
# todo implement load

class CMD:
    """
        comm: str: pitch, yaw, height, None
        amount: int: how much to move
    """

    def __init__(self, comm: str, amount: int = None):
        self.cmd = None
        self.amount = amount
        if comm not in cmds:
            print('bad cmd')
            self.cmd = ''
            self.amount = 0
        self.cmd = comm
        self.amount = amount

    def __repr__(self):
        return f"{self.cmd}::{self.amount}"

    def get_action(self) -> str:
        return self.cmd

    def get_amount(self) -> int:
        return self.amount

    @staticmethod
    def permitted_cmds():
        return cmds
