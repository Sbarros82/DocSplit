"""Blog público e administração de posts (dicas de uso)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import CurrentUser, get_optional_user
from api.routes_admin import require_admin

router = APIRouter(prefix="/api/blog", tags=["Blog"])


def _slugify(text: str) -> str:
    value = text.strip().lower()
    value = (
        value.replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value).strip("-")
    return value[:80] or f"post-{int(datetime.now().timestamp())}"


class BlogPostIn(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    excerpt: str = Field("", max_length=400)
    body_md: str = Field(..., min_length=10)
    slug: str | None = Field(None, max_length=100)
    published: bool = False
    cover_url: str | None = None


class BlogPostUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=160)
    excerpt: str | None = Field(None, max_length=400)
    body_md: str | None = Field(None, min_length=10)
    slug: str | None = Field(None, max_length=100)
    published: bool | None = None
    cover_url: str | None = None


def _public_fields(row: dict) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "slug": row.get("slug"),
        "title": row.get("title"),
        "excerpt": row.get("excerpt") or "",
        "body_md": row.get("body_md") or "",
        "cover_url": row.get("cover_url"),
        "published": bool(row.get("published")),
        "published_at": row.get("published_at"),
        "author_email": row.get("author_email"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


@router.get("/posts")
def list_posts(
    include_drafts: bool = False,
    user: CurrentUser | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Lista posts publicados (ou todos, se admin pedir drafts)."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    show_drafts = False
    if include_drafts and user is not None:
        try:
            from api.routes_admin import is_admin_user

            show_drafts = is_admin_user(user)
        except Exception:
            show_drafts = False

    query = sb.table("blog_posts").select("*")
    if show_drafts:
        rows = query.order("updated_at", desc=True).limit(100).execute().data or []
    else:
        rows = (
            query.eq("published", True)
            .order("published_at", desc=True)
            .limit(50)
            .execute()
            .data
            or []
        )
    return {"posts": [_public_fields(r) for r in rows]}


@router.get("/posts/{slug}")
def get_post(slug: str) -> dict[str, Any]:
    """Retorna um post publicado pelo slug."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    rows = (
        sb.table("blog_posts")
        .select("*")
        .eq("slug", slug)
        .eq("published", True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(404, "Post não encontrado.")
    return {"post": _public_fields(rows[0])}


@router.post("/admin/posts")
def create_post(
    body: BlogPostIn,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Cria post (rascunho ou publicado)."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    slug = _slugify(body.slug or body.title)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "slug": slug,
        "title": body.title.strip(),
        "excerpt": (body.excerpt or "").strip(),
        "body_md": body.body_md.strip(),
        "cover_url": body.cover_url,
        "published": body.published,
        "published_at": now if body.published else None,
        "author_email": admin.email,
        "created_at": now,
        "updated_at": now,
    }
    try:
        res = sb.table("blog_posts").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(400, f"Não foi possível criar o post (slug pode já existir): {exc}") from exc
    row = (res.data or [None])[0]
    if not row:
        raise HTTPException(500, "Falha ao criar post.")
    return {"post": _public_fields(row)}


@router.put("/admin/posts/{post_id}")
def update_post(
    post_id: str,
    body: BlogPostUpdate,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Atualiza post existente."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    existing = (
        sb.table("blog_posts").select("*").eq("id", post_id).limit(1).execute().data or []
    )
    if not existing:
        raise HTTPException(404, "Post não encontrado.")
    current = existing[0]
    updates: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.title is not None:
        updates["title"] = body.title.strip()
    if body.excerpt is not None:
        updates["excerpt"] = body.excerpt.strip()
    if body.body_md is not None:
        updates["body_md"] = body.body_md.strip()
    if body.cover_url is not None:
        updates["cover_url"] = body.cover_url
    if body.slug is not None:
        updates["slug"] = _slugify(body.slug)
    if body.published is not None:
        updates["published"] = body.published
        if body.published and not current.get("published_at"):
            updates["published_at"] = datetime.now(timezone.utc).isoformat()
        if not body.published:
            updates["published_at"] = None
    updates["author_email"] = admin.email or current.get("author_email")
    res = sb.table("blog_posts").update(updates).eq("id", post_id).execute()
    row = (res.data or [None])[0] or {**current, **updates}
    return {"post": _public_fields(row)}


@router.delete("/admin/posts/{post_id}")
def delete_post(
    post_id: str,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Remove um post."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    sb.table("blog_posts").delete().eq("id", post_id).execute()
    return {"success": True, "id": post_id}
