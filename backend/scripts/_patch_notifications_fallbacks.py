from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
p = ROOT / "frontend" / "src" / "pages" / "Notifications.jsx"
t = p.read_text(encoding="utf-8")
t = t.replace("{n.title}", "{n.title ?? 'Notification'}")
t = t.replace("{n.message}", "{n.message ?? '—'}")
# key fallback
t = t.replace("key={n.id || n._id}", "key={n.id || n._id || i}")
# only first occurrence per block - the replace all might break if multiple
# n.title appears twice? only one in map
p.write_text(t, encoding="utf-8")
print("notifications fallbacks")
