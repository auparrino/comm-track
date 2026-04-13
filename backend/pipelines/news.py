"""
Pisubí — Pipeline de Noticias
Fuentes: RSS feeds por commodity + diarios económicos AR (Ámbito, Cronista, iProfesional)
Clasificación: LLM (Groq → Cerebras → Mistral)

Uso:
  python -m backend.pipelines.news [--commodity all|lithium|gold|soy] [--no-classify]
  python -m backend.pipelines.news --reclassify          # re-clasifica artículos sin clasificar
  python -m backend.pipelines.news --reclassify --all    # re-clasifica todos (sobreescribe)
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import feedparser
import requests
from bs4 import BeautifulSoup

from backend.config import RSS_FEEDS, AR_ECONOMIC_FEEDS, DB_PATH
from backend.pipelines.base_pipeline import BasePipeline
from backend.pipelines.llm_client import llm


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _parse_date(entry) -> str | None:
    """Extrae fecha ISO desde un entry de feedparser."""
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    # fallback: feedparser struct_time
                    st = getattr(entry, f"{attr}_parsed", None)
                    if st:
                        return datetime(*st[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
    return None


def _clean_snippet(text: str | None, max_len: int = 600) -> str:
    """Limpia HTML y trunca."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ", strip=True)
    return clean[:max_len]


# ──────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────

class NewsPipeline(BasePipeline):
    """
    Descarga RSS, guarda artículos crudos y los clasifica con LLM.
    """

    def __init__(self):
        super().__init__("news")

    def _fetch_feed(self, url: str) -> list[dict]:
        """Descarga y parsea un feed RSS. Retorna lista de dicts normalizados."""
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Pisubí-Bot/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as exc:
            self.log(f"  RSS error {url}: {exc}")
            return []

        articles = []
        for entry in feed.entries:
            title   = getattr(entry, "title", "").strip()
            url_art = getattr(entry, "link", "").strip()
            snippet = _clean_snippet(
                getattr(entry, "summary", None) or getattr(entry, "description", None)
            )
            pub_at  = _parse_date(entry)
            source  = feed.feed.get("title", url.split("/")[2])

            if not title or not url_art:
                continue

            articles.append({
                "title":        title,
                "url":          url_art,
                "snippet":      snippet,
                "source":       source,
                "published_at": pub_at,
            })

        return articles

    def _save_article(self, conn, commodity_id: str, art: dict) -> int | None:
        """
        Inserta el artículo si no existe (url UNIQUE).
        Retorna el id insertado, o None si ya existía.
        """
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO news
                    (commodity_id, title, snippet, url, source, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    commodity_id,
                    art["title"],
                    art["snippet"],
                    art["url"],
                    art["source"],
                    art["published_at"],
                ),
            )
            if cur.lastrowid and cur.rowcount > 0:
                self._records_processed += 1
                return cur.lastrowid
            else:
                self._records_skipped += 1
                return None
        except Exception as exc:
            self.log(f"  DB error guardando '{art['title'][:40]}': {exc}")
            return None

    def _classify_article(self, conn, article_id: int, title: str, snippet: str) -> None:
        """Clasifica una noticia con LLM y actualiza la fila en DB.
        También corrige commodity_id si el LLM identifica uno específico.
        """
        try:
            result = llm.classify_news(title, snippet)

            # Inferir commodity_id desde la clasificación LLM
            # El LLM devuelve una lista como ["gold"] o ["lithium", "gold"]
            # Si hay un único commodity reconocido (no "other"), se usa ese.
            llm_commodities = [
                c for c in result.get("commodities", [])
                if c in ("lithium", "gold", "soy", "copper", "natgas", "wheat", "corn")
            ]
            new_commodity = llm_commodities[0] if len(llm_commodities) == 1 else None

            if new_commodity:
                conn.execute(
                    """
                    UPDATE news SET
                        commodity_id     = ?,
                        sentiment        = ?,
                        signal_type      = ?,
                        relevance_score  = ?,
                        summary_es       = ?,
                        impact_direction = ?,
                        llm_provider     = ?,
                        classified_at    = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        new_commodity,
                        result.get("sentiment"),
                        result.get("signal_type"),
                        result.get("relevance_score"),
                        result.get("summary_es"),
                        result.get("impact_direction"),
                        result.get("llm_provider"),
                        article_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE news SET
                        sentiment        = ?,
                        signal_type      = ?,
                        relevance_score  = ?,
                        summary_es       = ?,
                        impact_direction = ?,
                        llm_provider     = ?,
                        classified_at    = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        result.get("sentiment"),
                        result.get("signal_type"),
                        result.get("relevance_score"),
                        result.get("summary_es"),
                        result.get("impact_direction"),
                        result.get("llm_provider"),
                        article_id,
                    ),
                )
        except Exception as exc:
            self.log(f"  LLM error id={article_id}: {exc}")

    def _run_reclassify(self, conn, force_all: bool = False) -> None:
        """Re-clasifica artículos existentes en la DB.

        Si force_all=False solo procesa los que aún no tienen classified_at.
        Si force_all=True procesa todos (sobreescribe clasificaciones previas).
        """
        if force_all:
            rows = conn.execute(
                "SELECT id, title, snippet FROM news ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, snippet FROM news WHERE classified_at IS NULL ORDER BY id"
            ).fetchall()

        total = len(rows)
        if total == 0:
            self.log("No hay artículos pendientes de clasificación.")
            return

        self.log(f"Re-clasificando {total} artículos...")
        for i, (aid, title, snippet) in enumerate(rows, 1):
            self._classify_article(conn, aid, title or "", snippet or "")
            if i % 5 == 0:
                conn.commit()
                self.log(f"  {i}/{total} clasificados")
        conn.commit()
        self.log("Re-clasificación completa.")

    def run(self, commodity: str = "all", classify: bool = True) -> None:
        feeds = RSS_FEEDS if commodity == "all" else {
            k: v for k, v in RSS_FEEDS.items() if k == commodity
        }

        with self.get_conn() as conn:
            new_ids: list[tuple[int, str, str]] = []  # (id, title, snippet)

            # Feeds por commodity
            for commodity_id, urls in feeds.items():
                self.log(f"Commodity: {commodity_id} ({len(urls)} feeds)")
                for url in urls:
                    articles = self._fetch_feed(url)
                    self.log(f"  {url} -> {len(articles)} articulos")
                    for art in articles:
                        aid = self._save_article(conn, commodity_id, art)
                        if aid:
                            new_ids.append((aid, art["title"], art["snippet"]))

            # Feeds económicos AR (commodity_id=None, el LLM asigna)
            if commodity == "all":
                self.log(f"Feeds económicos AR ({len(AR_ECONOMIC_FEEDS)} feeds)")
                for url in AR_ECONOMIC_FEEDS:
                    articles = self._fetch_feed(url)
                    self.log(f"  {url} -> {len(articles)} articulos")
                    for art in articles:
                        aid = self._save_article(conn, None, art)
                        if aid:
                            new_ids.append((aid, art["title"], art["snippet"]))

            conn.commit()
            self.log(f"Guardados: {self._records_processed} nuevos, {self._records_skipped} duplicados")

            if classify and new_ids:
                self.log(f"Clasificando {len(new_ids)} artículos con LLM...")
                for i, (aid, title, snippet) in enumerate(new_ids, 1):
                    self._classify_article(conn, aid, title, snippet)
                    if i % 5 == 0:
                        conn.commit()
                        self.log(f"  {i}/{len(new_ids)} clasificados")
                conn.commit()
                self.log(f"Clasificación completa.")
            elif not classify:
                self.log("Clasificación LLM omitida (--no-classify).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de noticias Pisubí")
    parser.add_argument("--commodity", default="all",
                        choices=["all", "lithium", "gold", "soy", "copper", "natgas", "wheat", "corn"])
    parser.add_argument("--no-classify", action="store_true",
                        help="Saltar clasificación LLM")
    parser.add_argument("--reclassify", action="store_true",
                        help="Re-clasificar artículos sin clasificar (no descarga nuevos)")
    parser.add_argument("--all", dest="force_all", action="store_true",
                        help="Con --reclassify, sobreescribir clasificaciones existentes")
    args = parser.parse_args()

    pl = NewsPipeline()
    with pl.run_context():
        if args.reclassify:
            with pl.get_conn() as conn:
                pl._run_reclassify(conn, force_all=args.force_all)
        else:
            pl.run(commodity=args.commodity, classify=not args.no_classify)
