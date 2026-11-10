import json
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.exceptions import BizError
from app.models import User
from app.schemas.reservation import ReservationCreateRequest
from app.services import kb_service, lab_service, equipment_service, reservation_service


def build_tools(db:Session,current_user:User):
    @tool()
    def search_lab_docs(query:str):
        """查询实验室知识库，回答预约规则、开放时间、安全规范、设备使用等问题时使用

        Args:
            query: 检索问题，用一句完整的中文描述，例如"预约需要审核吗"
        """
        try:
            return kb_service.search(query) or "没有检索到内容"
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool()
    def list_open_labs(keywords:str="")->str:
        """查询当前开放（启用状态）的实验室列表，返回名称、位置、容量与开放时间

        Args:
            keywords: 实验室名称关键字，可为空字符串表示查全部
        """
        try:
            keywords=keywords.strip()
            page=lab_service.get_lab_page(db,page=1,name=keywords,page_size=10,status=1)
            rows = [
                {"id": item.id,
                 "name": item.name,
                 "location": item.location,
                 "capacity": item.capacity,
                 "open_time": item.open_time,
                 "close_time": item.close_time,
                 }
                for item in page.list
            ]
            return json.dumps({"total":page.total,"labs":rows}, ensure_ascii=False)
        except Exception as e:
                return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool()
    def list_lab_equipment(lab_id: int,keywords:str="") -> str:
        """查询某个实验室的设备列表，lab_id 从 list_open_labs 的结果中获取

        Args:
            lab_id: 实验室 ID，必须来自 list_open_labs 返回的 id
            keywords: 设备名称关键字，可为空字符串表示查全部
        """
        try:
            keywords=keywords.strip() or None
            page=equipment_service.get_equipment_page(db,lab_id=lab_id,page=1,page_size=10,name=keywords)
            rows = [
                {"id": item.id,
                 "name": item.name,
                 'lab_id': item.lab_id,
                 "lab_name": item.lab_name,
                 "quantity": item.quantity,
                 "spec": item.spec,
                 "status": item.status,
                 }
                for item in page.list
            ]
            return json.dumps({"total":page.total,"equipments":rows}, ensure_ascii=False)
        except Exception as e:
                return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool()
    def create_lab_reservation(lab_id: int, date: str, start_time: str,
                               end_time: str,equipment_id:int | None=None,remark:str | None=None) -> str:
        """为当前用户创建实验室/设备预约，提交后进入待审核状态。必须先向用户确认预约信息后才能调用

        Args:
            lab_id: 实验室 ID，来自 list_open_labs 返回的 id
            date: 预约日期，严格使用 YYYY-MM-DD 格式（可先调 get_today 换算"明天"等相对日期）
            start_time: 开始时间，严格使用 HH:mm 格式（24 小时制，如 09:00）
            end_time: 结束时间，严格使用 HH:mm 格式，必须晚于开始时间
            equipment_id: 设备 ID，来自 list_lab_equipment 返回的 id；预约整间实验室时不要传
            remark: 备注说明，可为空
        """
        try:
            data=ReservationCreateRequest(
                lab_id=lab_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id,
                remark=remark,
            )
            reservation_service.create_reservation(db,current_user,data)
            return json.dumps({"ok": True, "message": "预约已提交，请等待审核","lab_id":lab_id,
                               "date":date,"start_time":start_time,"end_time":end_time},
                              ensure_ascii=False)
        except BizError as e:
            return json.dumps({"ok": False, "error": str(e.message)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool()
    def get_today()->str:
        """查询今天的日期，返回 YYYY-MM-DD 格式；涉及"今天/明天/下周"等相对日期时先调用本工具"""
        return datetime.now().strftime("%Y-%m-%d")


    return [search_lab_docs,list_open_labs,list_lab_equipment,create_lab_reservation,get_today]



