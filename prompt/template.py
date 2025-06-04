from pathlib import Path

def inject_into_template(template_path: str, **fields) -> str:
    """
    Injects fields into a template file and returns the formatted content.
    """
    content = Path(template_path).read_text().format(**fields)
    return content

# print(inject_into_template(
#     "correct_sql.md",
#     question="123",
#     schema="321",
#     sql="121"
# ))