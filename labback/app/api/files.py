import os
import shutil
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from app.exceptions import BizError
from app.schemas.response import Result

file_router = APIRouter(prefix="/files",tags=["文件管理"])

@file_router.post("/upload")
def upload(file: UploadFile = File(...)):
    """上传文件"""
    #校验文件名
    if not file.filename:
        raise BizError(message="文件名不能为空")

    origin_name = os.path.basename(file.filename)
    #校验文件类型
    suffix = str(Path(origin_name).suffix.lower())
    if suffix not in ALLOWED_EXTENSIONS:
        raise BizError(message="文件类型不允许")

    # 校验文件大小：seek(0, 2) 把游标移到文件末尾得到总字节数，再移回开头

    if file.size and file.size > MAX_FILE_SIZE:
        raise BizError(message=f"文件过大，最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB")

    # 保存文件到 UPLOAD_DIR 并返回文件信息
    # 生成唯一文件名: 时间戳+随机数+文件类型
    disk_name = f"{int(time.time()*1000)}{uuid.uuid4().hex[:8]}{suffix}"
    # 保存文件到 UPLOAD_DIR 目录
    save_path=UPLOAD_DIR / disk_name
    with open(save_path, "wb") as f:
        #流式写入文件内容
        shutil.copyfileobj(file.file, f)

    return Result.success(data={"origin_name": origin_name,"file_name": disk_name,"size": file.size
                                ,"url": f"uploads/{disk_name}"
                                }
                          , message="文件上传成功")
