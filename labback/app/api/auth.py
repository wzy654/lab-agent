#登录接口，相当与controller

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.response import Result
from app.services import auth_service

auth_router = APIRouter(prefix="/auth",tags=["权限验证"])

@auth_router.post(path="/login", response_model=Result[LoginResponse])
def login(data: LoginRequest,db: Session = Depends(get_db)):
    return Result.success(data=auth_service.login(db, data), message="登录成功")


@auth_router.post(path="/register", response_model=Result[LoginResponse])
def register(data: RegisterRequest,db: Session = Depends(get_db)):
    """注册用户"""
    auth_service.register(db,data)
    return Result.success( message="注册成功")
