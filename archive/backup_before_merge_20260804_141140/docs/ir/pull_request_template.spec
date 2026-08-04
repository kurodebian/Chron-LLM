T: PR_Template = { content: Str, path: Str }
T: Repo = { templates: [PR_Template] }
S: repo: Repo
O: customize(t: PR_Template, c: Str) -> { ...t, content: c }
O: commit(r: Repo, t: PR_Template) -> { ...r, templates: [...r.templates, t] }
INV: use(t) -> exists(x in r.templates | x == t)
PRE(commit): t != null
POST(commit): t in r.templates