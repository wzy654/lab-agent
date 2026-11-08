# 集中导入所有模型：保证 Base.metadata 能注册到每张表，
# main.py 的 create_all 才会把这些表建出来（没被导入的模型会被忽略）
from .User import User
from .lab import Lab
from .equipment import Equipment
from .reservation import Reservation

__all__ = ["User", "Lab", "Equipment", "Reservation"]
