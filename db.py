from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_order(user_id: int, username: str, description: str, topic_id: int) -> None:
    """Создать заказ и сохранить привязку к теме форума."""
    supabase.table("orders").insert({
        "user_id": user_id,
        "username": username,
        "description": description,
        "topic_id": topic_id,
        "status": "active",
    }).execute()


def get_order_by_topic(topic_id: int) -> dict | None:
    """Найти заказ по id темы форума."""
    result = supabase.table("orders").select("*").eq("topic_id", topic_id).execute()
    return result.data[0] if result.data else None


def get_order_by_user(user_id: int) -> dict | None:
    """Найти активный заказ пользователя."""
    result = (
        supabase.table("orders")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .execute()
    )
    return result.data[0] if result.data else None


def get_active_orders() -> list[dict]:
    """Все активные заказы (для кнопки «Мои заказы»)."""
    result = supabase.table("orders").select("*").eq("status", "active").execute()
    return result.data


def delete_order(topic_id: int) -> None:
    """Удалить заказ и его данные по id темы (чистка после завершения)."""
    supabase.table("orders").delete().eq("topic_id", topic_id).execute()
