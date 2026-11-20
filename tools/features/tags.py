"""Tag vocabulary helpers shared by the build and validation steps."""

from __future__ import annotations


def tag_map(meta: dict) -> dict[str, dict]:
    return {tag["slug"]: tag for tag in meta.get("tags", [])}


def tag_name(meta: dict, slug: str) -> str:
    tag = tag_map(meta).get(slug)
    return tag["name"] if tag else slug


def courses_for_tag(courses: list[dict], slug: str) -> list[dict]:
    return [course for course in courses if slug in course.get("tags", [])]


def tag_counts(meta: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for course in meta.get("courses", []):
        for slug in course.get("tags", []):
            counts[slug] = counts.get(slug, 0) + 1
    return counts
