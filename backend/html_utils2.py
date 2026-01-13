from html_mor_utils import create_report_pdf
from pathlib import Path


font_geneva = {"fontname": "Calibri"}
textbox_kwargs = {
    "backgroundcolor": "#242526",
    "alpha": 0.8,
    "color": "white",
    "fontweight": 900,
    "multialignment": "center",
    "horizontalalignment": "center",
    "fontsize": 16,
}
textbox_kwargs.update(font_geneva)
font_geneva_title = {"fontname": "Calibri", "weight": "bold", "fontsize": 20}
sum = 0
decs = 0


def get_template_path(key: str, templates: dict[str, str | Path] | str | Path):
    if isinstance(templates, str):
        return Path(templates)
    elif isinstance(templates, Path):
        return templates
    return templates.get(key)
