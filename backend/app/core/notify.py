"""企业微信群机器人推送工具

使用方法：
  在群机器人设置中复制 Webhook URL，填入 .env 的 WXWORK_WEBHOOK_URL。
  调用 notify(text) 或更具体的 notify_contract / notify_task 函数。
  推送失败只记录日志，不影响主流程。
"""

import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def notify(content: str) -> None:
    """发送纯文本消息到企业微信群机器人，失败静默处理。"""
    url = settings.WXWORK_WEBHOOK_URL
    if not url:
        return
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if data.get("errcode") != 0:
                logger.warning("企业微信推送失败: %s", data)
    except Exception as e:
        logger.warning("企业微信推送异常: %s", e)


async def notify_contract(contract_no: str, contract_name: str, amount: float, creator: str) -> None:
    content = (
        f"📄 新合同已创建\n"
        f"合同编号：{contract_no}\n"
        f"合同名称：{contract_name}\n"
        f"合同金额：¥{amount:,.2f}\n"
        f"创建人：{creator}"
    )
    await notify(content)


async def notify_task(task_name: str, project_no: str, assigned_to: str, planned_end: str) -> None:
    content = (
        f"📋 新任务已创建\n"
        f"任务名称：{task_name}\n"
        f"所属项目：{project_no}\n"
        f"负责人：{assigned_to}\n"
        f"计划完成：{planned_end}"
    )
    await notify(content)
