from django.conf import settings


def site_meta(_request):
    return {
        "SITE_ORIGIN": getattr(settings, "SITE_ORIGIN", ""),
        "SITE_NAME": getattr(settings, "SITE_NAME", "Advising"),
        "SITE_DESCRIPTION": getattr(
            settings,
            "SITE_DESCRIPTION",
            "Advising — a clean, accessible Django 5 + Tailwind v4 starter.",
        ),
    }
