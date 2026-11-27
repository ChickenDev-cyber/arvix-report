---
kernelspec:
  name: python3
  display_name: Python 3
---
# Chương 3 — Milestone 3: Đối sánh thực thể trích dẫn (Matching)

> **Người phụ trách:** Minh Trọng (`@ChickenDev-cyber`)  
> **Reviewer:** Huy Hoàng (`huynhhuyhoang2006@gmail.com`)

Chương 3 trình bày bài toán xếp hạng và đối sánh thực thể trích dẫn từ cây cú pháp Milestone 2 sang kho tham chiếu Milestone 1 theo nguyên tắc **Zero External Knowledge**.

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m3 = unified.load_json("m3_unified_summary")
splits = m3["pool_and_split"]["split_counts"]
labels = list(splits.keys())
vals = list(splits.values())
fig = go.Figure(go.Bar(x=labels, y=vals, text=[str(v) for v in vals], textposition="outside"))
fig.update_layout(
    title="Phân bố số bài báo theo tập (train / valid / test)",
    xaxis_title="Tập dữ liệu",
    yaxis_title="Số bài báo",
    template="plotly_white",
    margin=dict(t=50, b=40, l=50, r=20),
)
unified.render_plotly(fig, height=340)
```
