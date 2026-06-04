import asyncio
import base64
import json
from api.workers.celery_app import celery_app
from api.core.config import settings


@celery_app.task(name="browsing.run_browsing_task", bind=True, max_retries=1)
def run_browsing_task(self, task_id: str):
    asyncio.run(_run_browsing_task_async(task_id))


async def _run_browsing_task_async(task_id: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, update
    from api.models.browsing import BrowsingTask
    from api.core.openrouter import openrouter_client
    from api.services.webhook import fire_webhook, dispatch_event
    from playwright.async_api import async_playwright

    engine = create_async_engine(settings.database_url)
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as db:
        result = await db.execute(select(BrowsingTask).where(BrowsingTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return
        await db.execute(update(BrowsingTask).where(BrowsingTask.id == task_id).values(status="running"))
        await db.commit()

    trajectory = []
    final_result = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            await page.goto(task.start_url)
            messages = [{"role": "user", "content": f"Task: {task.task}\nCurrent URL: {task.start_url}"}]
            model = task.agent or settings.sentinel_vision_model

            for step in range(task.max_steps):
                screenshot_bytes = await page.screenshot(type="webp")
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                messages_with_screenshot = messages + [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/webp;base64,{screenshot_b64}"}},
                        {"type": "text", "text": f"Current URL: {page.url}. What action should I take?"},
                    ]
                }]
                response = await openrouter_client.chat_completions({
                    "model": model,
                    "messages": messages_with_screenshot,
                    "max_completion_tokens": 512,
                    "temperature": 0.3,
                })
                choice = response["choices"][0]["message"]
                tool_calls = choice.get("tool_calls") or []
                content = choice.get("content", "")
                trajectory.append({"step": step, "url": page.url, "action": tool_calls[0]["function"]["name"] if tool_calls else "done", "reasoning": content})
                if not tool_calls:
                    final_result = content
                    break
                for tc in tool_calls:
                    action_name = tc["function"]["name"]
                    args = json.loads(tc["function"].get("arguments", "{}"))
                    await _execute_action(page, action_name, args)
                messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
                messages.append({"role": "tool", "tool_call_id": tool_calls[0]["id"], "content": f"Action {action_name} executed. Current URL: {page.url}"})

            if not final_result:
                final_result = f"Completed {len(trajectory)} steps on {page.url}"
            await browser.close()

    except Exception as e:
        async with AsyncSession() as db:
            await db.execute(update(BrowsingTask).where(BrowsingTask.id == task_id).values(status="failed", result=str(e), trajectory=trajectory))
            await db.commit()
            event_type = "browsing.failed"
            event_payload = {
                "event": event_type,
                "task_id": task_id,
                "status": "failed",
                "result": str(e),
            }
            await dispatch_event(db, event_type, event_payload)
        await engine.dispose()
        raise

    async with AsyncSession() as db:
        task_row = await db.execute(select(BrowsingTask).where(BrowsingTask.id == task_id))
        task = task_row.scalar_one()
        await db.execute(update(BrowsingTask).where(BrowsingTask.id == task_id).values(status="succeeded", result=final_result, trajectory=trajectory))
        await db.commit()
        event_type = "browsing.completed"
        event_payload = {
            "event": event_type,
            "task_id": task.id,
            "status": "succeeded",
            "result": final_result,
        }
        await dispatch_event(db, event_type, event_payload)
        if task.webhook_url:
            await fire_webhook(task.webhook_url, task.webhook_format, {"task_id": task_id, "status": "succeeded", "result": final_result})
    await engine.dispose()


async def _execute_action(page, action: str, args: dict):
    coords = args.get("coordinates", [500, 400])
    x, y = int(coords[0] * 1280 / 1000), int(coords[1] * 800 / 1000)
    actions = {
        "left_click": lambda: page.mouse.click(x, y),
        "double_click": lambda: page.mouse.dblclick(x, y),
        "right_click": lambda: page.mouse.click(x, y, button="right"),
        "type": lambda: page.keyboard.type(args.get("text", "")),
        "key_press": lambda: page.keyboard.press(args.get("key", "Enter")),
        "scroll": lambda: page.mouse.wheel(0, 300 if args.get("direction", "down") == "down" else -300),
        "goto_url": lambda: page.goto(args.get("url", "")),
        "go_back": lambda: page.go_back(),
        "go_forward": lambda: page.go_forward(),
        "refresh": lambda: page.reload(),
        "wait": lambda: asyncio.sleep(args.get("duration", 1)),
    }
    fn = actions.get(action)
    if fn:
        await fn()
