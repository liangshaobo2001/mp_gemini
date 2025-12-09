from typing import Dict, Any, List

class LayoutParser:
    def __init__(self):
        pass

    def parse_wireframe(self, wireframe_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Parses a wireframe JSON and returns a dictionary of filename -> content.
        """
        sections = wireframe_data.get("sections", [])
        html_content = self._generate_html(sections)
        css_content = self._generate_css()
        
        return {
            "index.html": html_content,
            "style.css": css_content
        }

    def _generate_html(self, sections: List[Dict[str, Any]]) -> str:
        body_content = ""
        for section in sections:
            s_type = section.get("type")
            if s_type == "navbar":
                links = section.get("links", ["Home"])
                links_html = "".join([f'<a href="#">{link}</a>' for link in links])
                body_content += f'<nav class="navbar">{links_html}</nav>\n'
            elif s_type == "hero":
                title = section.get("title", "Hero Title")
                subtitle = section.get("subtitle", "")
                bg_image = section.get("backgroundImage", "")
                style_attr = f' style="background-image: url(\'{bg_image}\'); background-size: cover;"' if bg_image else ""
                body_content += f'<header class="hero"{style_attr}><h1>{title}</h1><p>{subtitle}</p></header>\n'
            elif s_type == "footer":
                text = section.get("text", "Footer Text")
                body_content += f'<footer class="footer"><p>{text}</p></footer>\n'
            elif s_type == "grid":
                items = section.get("items", 3)
                grid_items = "".join([f'<div class="card">Item {i+1}</div>' for i in range(items)])
                body_content += f'<section class="grid">{grid_items}</section>\n'
            elif s_type == "sidebar":
                links = section.get("links", ["Link 1", "Link 2"])
                links_html = "".join([f'<li><a href="#">{link}</a></li>' for link in links])
                body_content += f'<aside class="sidebar"><ul>{links_html}</ul></aside>\n'
            elif s_type == "form":
                fields = section.get("fields", ["Name", "Email"])
                fields_html = "".join([f'<div class="form-group"><label>{field}</label><input type="text" placeholder="{field}"></div>' for field in fields])
                body_content += f'<form class="form">{fields_html}<button type="submit">Submit</button></form>\n'
            elif s_type == "gallery":
                images = section.get("images", 3)
                gallery_items = "".join([f'<div class="gallery-item"><img src="https://via.placeholder.com/150" alt="Image {i+1}"></div>' for i in range(images)])
                body_content += f'<section class="gallery">{gallery_items}</section>\n'
            else:
                # Fallback for unknown sections
                body_content += f'<section class="generic-section"><h2>{s_type.capitalize() if s_type else "Section"}</h2><p>Placeholder for {s_type}</p></section>\n'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Wireframe</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
{body_content}
</body>
</html>"""

    def _generate_css(self) -> str:
        return """
body { font-family: sans-serif; margin: 0; padding: 0; }
.navbar { background: #333; color: white; padding: 1rem; }
.navbar a { color: white; margin-right: 1rem; text-decoration: none; }
.hero { background: #f4f4f4; padding: 4rem 2rem; text-align: center; }
.footer { background: #333; color: white; padding: 1rem; text-align: center; margin-top: 2rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; padding: 2rem; }
.card { border: 1px solid #ddd; padding: 1rem; border-radius: 4px; }
.sidebar { width: 250px; background: #f0f0f0; padding: 1rem; float: left; }
.form { max_width: 600px; margin: 2rem auto; padding: 1rem; border: 1px solid #ccc; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; }
.form-group input { width: 100%; padding: 0.5rem; }
.gallery { display: flex; flex-wrap: wrap; gap: 1rem; padding: 2rem; }
.gallery-item img { max_width: 100%; height: auto; }
.generic-section { padding: 2rem; border: 1px dashed #ccc; margin: 1rem; text-align: center; }
"""
