import os
import re
from bs4 import BeautifulSoup
import tinycss2

TEMPLATE_DIR = "templates"
STATIC_DIR = "static"
CSS_PATH = os.path.join(STATIC_DIR, "styles.css")

def extract_used_selectors_from_html():
    used_classes = set()
    used_ids = set()

    for root, _, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    for tag in soup.find_all(True):
                        cls = tag.get("class")
                        if cls:
                            used_classes.update(cls)
                        id_ = tag.get("id")
                        if id_:
                            used_ids.add(id_)
    return used_classes, used_ids

def extract_used_selectors_from_js():
    used_classes = set()
    used_ids = set()

    js_pattern = re.compile(r"""(?:
        classList\.(?:add|remove|toggle)\(["']([\w\-_ ]+)["']\) |
        setAttribute\(["']class["'],\s*["']([\w\-_ ]+)["']\) |
        getElementById\(["']([\w\-_]+)["']\) |
        [#\.]([\w\-_]+)  # selectors like '.popup' or '#modal'
    )""", re.VERBOSE)

    for root, _, files in os.walk(STATIC_DIR):
        for file in files:
            if file.endswith(".js"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                    matches = js_pattern.findall(text)
                    for match in matches:
                        for i, group in enumerate(match):
                            if group:
                                if i == 0 or i == 1 or i == 3:
                                    used_classes.update(group.strip().split())
                                elif i == 2:
                                    used_ids.add(group.strip())
    return used_classes, used_ids

def extract_defined_selectors_from_css(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    rules = tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True)

    defined_classes = set()
    defined_ids = set()

    for rule in rules:
        if rule.type == "qualified-rule":
            prelude = tinycss2.serialize(rule.prelude)
            selectors = re.findall(r'([#.])([\w\-_]+)', prelude)
            for symbol, name in selectors:
                if symbol == ".":
                    defined_classes.add(name)
                elif symbol == "#":
                    defined_ids.add(name)
    return defined_classes, defined_ids

def main():
    html_classes, html_ids = extract_used_selectors_from_html()
    js_classes, js_ids = extract_used_selectors_from_js()

    used_classes = html_classes.union(js_classes)
    used_ids = html_ids.union(js_ids)

    defined_classes, defined_ids = extract_defined_selectors_from_css(CSS_PATH)

    unused_classes = defined_classes - used_classes
    unused_ids = defined_ids - used_ids

    print("\n=== UNUSED CSS CLASSES ===")
    for cls in sorted(unused_classes):
        print(f".{cls}")

    print("\n=== UNUSED CSS IDS ===")
    for id_ in sorted(unused_ids):
        print(f"#{id_}")

if __name__ == "__main__":
    main()

