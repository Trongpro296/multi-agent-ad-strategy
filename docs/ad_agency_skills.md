# Skills nghiệp vụ cho AI Advertising Agency

18 skill quảng cáo nằm trong `.agents/skills/` của ChatDev, không phải thư mục skill cá nhân của Codex: 13 skill vai trò trong bảng dưới và 5 skill bổ sung. YAML chính đã gắn các skill bổ sung theo vai trò; bản auto có thể giữ allowlist nhỏ hơn. Xem hướng dẫn vận hành để biết cấu hình cụ thể. Skill là hướng dẫn nghiệp vụ, không thay Gate/runtime và không cung cấp quyền/công cụ còn thiếu.

| Node | Skill | File do node tạo |
|---|---|---|
| `Director_Brief` | [ad-brief-planning](../.agents/skills/ad-brief-planning/SKILL.md) | `campaign_brief.json` |
| `Market_Researcher` | [ad-market-research](../.agents/skills/ad-market-research/SKILL.md) | `market_research.md` |
| `Competitor_Analyst` | [ad-competitor-analysis](../.agents/skills/ad-competitor-analysis/SKILL.md) | `competitor_analysis.md` |
| `Customer_Insight` | [ad-customer-insight](../.agents/skills/ad-customer-insight/SKILL.md) | `audience_segments.json`, `customer_journey.md` |
| `Evidence_Digest` | [ad-evidence-synthesis](../.agents/skills/ad-evidence-synthesis/SKILL.md) | `evidence_digest.md`, `sources.csv` |
| `Brand_Strategist` | [ad-brand-positioning](../.agents/skills/ad-brand-positioning/SKILL.md) | `brand_positioning.md` |
| `Director_Strategy` | [ad-campaign-strategy](../.agents/skills/ad-campaign-strategy/SKILL.md) | `campaign_strategy.md`, `strategy_ids.json` |
| `Media_Planner` | [ad-media-planning](../.agents/skills/ad-media-planning/SKILL.md) | `media_plan.csv`, `budget_scenarios.csv` |
| `Creative_Director` | [ad-creative-direction](../.agents/skills/ad-creative-direction/SKILL.md) | `creative_brief.md`, `creative_matrix.csv` |
| `Performance_Analyst` | [ad-measurement-experiments](../.agents/skills/ad-measurement-experiments/SKILL.md) | `measurement_plan.md`, `experiment_plan.csv` |
| `Plan_Assembler` | [ad-plan-assembly-rework](../.agents/skills/ad-plan-assembly-rework/SKILL.md) | `advertising_strategy_draft.md`, `execution_calendar.csv` |
| `Strategy_QA` | [ad-strategy-quality-review](../.agents/skills/ad-strategy-quality-review/SKILL.md) | `qa_report.json` |
| `Delivery_Packager` | [ad-handoff-notes](../.agents/skills/ad-handoff-notes/SKILL.md) | `handoff_notes.md` |

## Cách ChatDev dùng skill

Khi bật Skills, runtime tự đưa activate_skill/read_skill_file vào danh sách tool nội bộ và chỉ liệt kê skill được allow. Agent gọi activate_skill; runtime đọc SKILL.md, đưa toàn bộ hướng dẫn vào system message rồi tiếp tục nhiệm vụ. Không cần tự thêm activate_skill vào Tooling trong UI.

Mỗi node chỉ được xem skill của mình, không lộ ba skill demo sẵn có. Không khai báo allowed-tools trong frontmatter vì trường này sẽ hạn chế tools khi skill active; các tools đang gắn ở YAML và quyền runtime tiếp tục quyết định khả năng thực thi.

Activation là tool nội bộ chạy local nhưng thông thường làm thêm một lượt model để nhận hướng dẫn rồi tiếp tục. Chưa đo token/model thật trong lần tạo này; không có cam kết skill sẽ làm tổng token giảm. Đã tránh bắt đọc nhiều tài liệu tham chiếu hoặc kích hoạt nhiều skill trong một node.

## Kiểm tra trước khi chạy

```powershell
uv run python tools/preflight_ad_agency.py
uv run python -m pytest tests/test_ad_agency_skills.py -q
```

Kiểm tra ngoại tuyến gồm parser, discovery/allowlist, activation và luồng executor với provider giả lập; không gọi model. Refresh và mở lại YAML mới trong editor. Trong phiên thật, kiểm tra log node có activate_skill thành công trước load_file/save_file. Đây vẫn là hành vi cần quan sát với model thật; bật config không tự bảo đảm mọi model sẽ tuân thủ.

Trong UI từng Agent: Advanced Settings → Agent Skills → enabled=true, Allow chứa skill vai trò ở bảng và các skill bổ sung phù hợp bên dưới. Main và auto đã có cấu hình skills; có thể có allowlist khác nhau. Không mặc định phase1/workflow demo có cấu hình giống bản đầy đủ. Bản auto vẫn cần ba biến MODEL_*.

## Skill bổ sung

| Skill | Gắn cho Agent |
|---|---|
| `ad-data-contracts` | `Media_Planner`, `Performance_Analyst`, `Plan_Assembler` |
| `ad-budget-feasibility` | `Director_Strategy`, `Media_Planner`, `Strategy_QA` |
| `ad-tracking-readiness` | `Performance_Analyst`, `Strategy_QA` |
| `ad-claims-review` | `Evidence_Digest`, `Creative_Director`, `Strategy_QA` |
| `ad-campaign-learning` | `Director_Strategy`, `Media_Planner`, `Performance_Analyst`; chỉ áp dụng khi có dữ liệu kết quả thật |

Xem [hướng dẫn vận hành](../ad_agency_v2_guide.md) để biết chi tiết tools, cách thêm skills và ánh xạ lấy từ YAML chính. Có skill không đồng nghĩa đã có kết nối với tài khoản quảng cáo hoặc có dữ liệu hiệu quả thực tế.

## Kết quả kiểm chứng 13/11/2026

- 13/13 SKILL.md qua quick_validate và parser của ChatDev.
- 83 ca hồi quy tập trung đạt: 27 ca skill, 8 nhóm Router/engine và 48 ca audit trước. Không chạy lại toàn bộ test repository trong lần thêm skill này.
- Executor thật dùng provider giả lập đã kích hoạt skill Evidence, gọi save_file hai lần, load_file hai lần, kiểm tra đủ hai file và CSV có UTF-8 BOM. Không gọi model/Serper và không chạy chiến dịch.
- Preflight bản chính xác nhận 13 Agent discover/activate được skill và trả OK. Test ngoại tuyến không chứng minh chất lượng nghiệp vụ của model thật.
- Log và backup kiểm tra cũ đã được dọn, không phải tài nguyên bắt buộc của dự án. Có thể chạy lại kiểm thử local khi cần.
