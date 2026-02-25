"""YF — Career Exploration (standalone entry point).

This file launches the Career Exploration wizard as the default landing page.
All logic lives in app.py; this is a thin wrapper that sets the default page.
"""

from app import main  # noqa: F401 – imports trigger st.set_page_config etc.

main(default_page="career_exploration")
