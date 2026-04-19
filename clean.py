import re
from pathlib import Path

root = Path(".")
tex_path = root / "CV" / "resume.tex"
cls_path = root / "CV" / "resume.cls"
out_tex = root / "public" / "cv" / "resume.cleaned.tex"
out_title = root / "public" / "cv" / "title.txt"
COMMAND_ARITY = {"csection": 2, "frcontent": 4, "clink": 1}

source = tex_path.read_text(encoding="utf-8")
cls_source = cls_path.read_text(encoding="utf-8")

if not all(token in cls_source for token in COMMAND_ARITY):
    raise RuntimeError("resume.cls must define csection/frcontent/clink")

cls_source = re.sub(r"^.*\\LoadClass.*$\n?", "", cls_source, flags=re.MULTILINE)
cls_source = re.sub(r"^.*\\LoadClass.*$\n?", "", cls_source, flags=re.MULTILINE)

title_re = r"\\Large\{([^{}]+)\}"
title_match = re.search(title_re, source)
page_title = (title_match.group(1).strip()) if title_match else ""

if "\\begin{document}" in source and "\\end{document}" in source:
    source = source.split("\\begin{document}", 1)[1]
    source = source.rsplit("\\end{document}", 1)[0]

source = re.sub(r"^(.*)%.*$", r"\1", source, flags=re.MULTILINE)
source = re.sub(r"^&\s*$\n?", "", source, flags=re.MULTILINE)
source = re.sub(title_re + ".*$\n?", "", source, flags=re.MULTILINE)
source = source.replace("\\fontfamily{ppl}\\selectfont", "")
source = source.replace("\\noindent", "")

source = re.sub(r'\\begin\{tabularx\}.*\\end\{tabularx\}', lambda m: m.group().replace('\\newline', '\\\\'), source, flags=re.DOTALL)
source = re.sub(r"^.*\\begin\{tabularx\}.*$\n?", "", source, flags=re.MULTILINE)
source = re.sub(r"^.*\\end\{tabularx\}.*$\n?", "", source, flags=re.MULTILINE)
source = source.replace("\\begin{center}", "")
source = source.replace("\\end{center}", "")
# source = re.sub(r"([^\\])(&)", r"\1\n", source)

def parse_braced(text: str, i: int):
    if i >= len(text) or text[i] != "{":
        return "", i
    i += 1
    depth = 1
    start = i
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2 if i + 1 < len(text) else 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    return text[start:], len(text)

def expand_command(text: str, command: str, nargs: int, renderer):
    out = []
    i = 0
    token = "\\" + command
    n = len(text)
    while i < n:
        j = text.find(token, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        k = j + len(token)
        while k < n and text[k].isspace():
            k += 1
        args = []
        ok = True
        for _ in range(nargs):
            while k < n and text[k].isspace():
                k += 1
            if k >= n or text[k] != "{":
                ok = False
                break
            arg, k = parse_braced(text, k)
            args.append(arg.strip())
        if ok:
            out.append(renderer(args))
            i = k
        else:
            out.append(token)
            i = j + len(token)
    return "".join(out)

def render_csection(args):
    title, body = args
    return f"\\section*{{{title}}}\n{body}\n"

def render_frcontent(args):
    first, second, third, fourth = args
    parts = [f"\\textbf{{{first}}}"]
    if second:
        parts.append(second)
    if third:
        parts.append(third)
    if fourth:
        parts.append(f"\\textit{{{fourth}}}")
    return " \\\\\n".join(parts) + "\n\n"

source = expand_command(source, "csection", COMMAND_ARITY["csection"], render_csection)
source = expand_command(source, "frcontent", COMMAND_ARITY["frcontent"], render_frcontent)
source = expand_command(source, "clink", COMMAND_ARITY["clink"], lambda a: a[0])

source = re.sub(r"\\vspace\*?\{[^}]*\}", "", source)
# source = re.sub(r"\\includegraphics(?:\[[^]]*\])?\{[^}]*\}", "", source)
source = re.sub(r"\n{3,}", "\n\n", source).strip()

cleaned = (
    "\\documentclass[14pt]{extreport}\n"
    "\\usepackage[margin=1in]{geometry}\n"
    "\\usepackage{hyperref}\n"
    "\\usepackage{graphicx}\n"
    "\\usepackage[utf8]{inputenc}\n"
    # + cls_source
    # + "\\newenvironment{cleanfrcontent}[4]{\n"
    # + "    {\n"
    # + "        \\textbf{#1}\\\\\n"
    # + "        #2\\\\\n"
    # + "        #3\\\\\n"
    # + "        \\textit{#4}\n"
    # + "    }\n"
    # + "}{}\n\n"
    + "\\begin{document}\n\n"
    + source
    + "\n\n\\end{document}\n"
)
out_tex.write_text(cleaned, encoding="utf-8")
out_title.write_text(page_title, encoding="utf-8")
