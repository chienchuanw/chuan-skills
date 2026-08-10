# Proposal — 開發工作流優化（四條）

> 產出自 2026-08-10 的 grilling session。目標：降低具體任務的**摩擦 (a)**、讓既有 skill **穩定觸發 (d)**。
> 非 FOMO——不是「學更多 skill」，而是把已擁有的能力接成可靠的自動化迴圈。
> **執行順序：③ → ② → ① → ④**（每條約一個開發 session）。

---

## 背景與原則

- 診斷結論：Chuan 不缺 skill（34 local + 一堆 external + 21KB `workflow.md`）。缺的是**自動化迴圈**與**觸發一致性**。
- 對應資產：`workflow.md` 的 7 階段流程、視覺化於 `~/Documents/Mind/Dev/chuan-skills-workflow.canvas`。
- 相容性硬約束：Chuan 的 global CLAUDE.md 要求「不可逆／大影響動作前先解釋 blast radius 並等確認」。本 spec 的 ① 用**護欄＋repo 硬性保護**在此約束下換取自主性。

---

## ③ 模型／effort 建議（先做，馬上可用）

**Goal**：在該做決定的時刻，得到「用什麼模型＋哪種 effort」的明確建議，而不是一個模型／一個 effort 一路用到底。

**決策（鎖定）**：形態 = (C) 混合。brainstorming 是外部 skill 不方便改，所以：
- **`handoff-prompt` 產出時**，自動附上「下一段建議用 X 模型 ／ Y effort ＋理由」。
- 新增輕量 **`/model-advisor`** skill，供 spec 討論前手動喊。
- 兩者共用同一張 rubric。

**要做**：
1. 定義 rubric（下方草案，實作時再校準）。
2. 新增 `plugins/dev/skills/model-advisor/SKILL.md`：問 2–4 題（任務複雜度？可逆嗎？context 會很大嗎？在意成本/速度嗎？）→ 依 rubric 給模型＋effort＋一句理由。
3. 改 `plugins/dev/skills/handoff-prompt/SKILL.md`：在輸出的接棒 prompt 裡加一段「建議模型／effort」，依同一 rubric。

**Rubric 草案（任務類型 → 模型 · effort）**：

| 任務類型 | 建議 | 理由 |
|---|---|---|
| 腦力激盪／spec／架構決策 | Opus · high effort | 解空間廣、要深推理 |
| 依明確計畫的直球實作 | Sonnet · medium | 計畫已定，求快與省 |
| 機械式編輯／改名／樣板 | Haiku/Sonnet · low | 低風險、可逆 |
| 棘手 bug 系統性除錯 | Opus · high | systematic-debugging 吃深推理 |
| code review sub-agent | Opus/Sonnet · high | 客觀性與正確性優先 |
| 大量檔案理解 | Opus(1M) · medium | 需大 context |
| handoff prompt 產生本身 | Haiku/Sonnet · low | 純轉述，低風險 |

> 加權訊號：**可逆性越低 → 模型/effort 越高**（如 ① 自動 merge 的決策）；**context 越大 → 選 1M 模型**。

**Acceptance**：`/model-advisor` 能對一個真實任務吐出具體建議；`handoff-prompt` 的輸出含模型/effort 段落。

---

## ② context 快滿／spec 後 → 穩定 handoff（第二做）

**Goal**：spec 討論定稿、context 已吃掉大半時，**穩定**產出「/clear 後新 session 該貼的接棒 prompt」。這是 (d) 觸發一致性問題，工具已存在（`handoff-prompt`）。

**要做**：
1. 檢視現有 `handoff-prompt` skill 的觸發描述，強化「spec 定稿後／context 接近上限時」這個時機的觸發語，讓 using-superpowers 更容易在對的時刻建議它。
2. 確認接棒 prompt 內容完整：目標、已定 spec 摘要、已完成/待辦、關鍵檔案、下一步第一個動作、（來自 ③）建議模型/effort。
3. 與 ③ 綁定：handoff 產出即帶模型/effort 建議。

**Acceptance**：在一個 context 偏滿的 session 尾聲喊 handoff，得到可直接貼進新 session 的自足 prompt。

---

## ① 自主 review → 自修/重構 → merge（第三做，最謹慎）

**Goal**：agent 自派 code-review sub-agent（客觀）、自修/重構、綠燈就 rebase merge，只有真正要決策時停下找 Chuan。Chuan 以**產出結果**確認、不細讀 PR。

**決策（鎖定）**：自主等級 = (A) 全自主到 merge，安全靠**護欄＋完整版控**。

**五條護欄（全收）**：
1. 只自動 merge 到 `dev`／整合分支，**永不自動碰 `main`/production**（釋出永遠是手動一步）。
2. 每次 merge = 一個可 revert 單位（squash／乾淨 rebase）＋記 commit/tag，退回 = `git revert <sha>`。
3. 絕不 force-push 共享分支。
4. merge 前置硬條件 = 客觀綠燈：**測試全過 ＋ review sub-agent 無 blocking**；任一沒過就停下找人。
5. 每次 merge 留一行紀錄（做了什麼／review 結論／如何 revert）＝「看結果」入口，取代讀 PR。

**GitHub repo 端硬性保護（建議設定，per repo）**：
- 保護 `main`：require pull request before merging、require status checks to pass（綁 CI/測試）、require linear history。
- 禁止 `main` 的 force-push 與刪除。
- （視情況）require conversation resolution；限制可推 main 的人。
- CI 提供 status check 讓護欄第 4 條的「綠燈」有 repo 端依據。

**要做**：
1. 設計自主迴圈（可能落成 `dev/feature` orchestrator 的擴充，或新 skill）：review(sub-agent) → fix/refactor → 測試 → 綠燈判定 → rebase merge 到 dev → 留紀錄。
2. 停機條件明確化：紅燈、需架構決策、跨檔案大重構取捨 → 停下附建議給 Chuan 討論。
3. 產出一份 GitHub branch-protection 設定清單／腳本（`gh api` 可自動套用）。

**Acceptance**：對一個真實 feature 分支，agent 能自主跑完 review→修→綠燈→merge 到 dev 並留紀錄；失敗情境會正確停機；main 受 repo rule 保護。

---

## ④ UI/UX 專案：視覺優先閘門 ＋ Figma 常態 sync（最後做）

**Goal**：有畫面的專案，先確認視覺美學才進碼；Figma design 與專案視覺常態同步。

**決策（鎖定）**：
- **Figma = source of truth**（5-1 A）：先在 Figma 定稿→Figma MCP 拉 design context/tokens 進來實作→畫面在碼裡改了要回推 Figma。
- **常態 sync 綁「動到 UI 的 PR」**（5-2）：UI 專案的 ① merge 前綠燈**多一關**——附截圖／臨時網頁連結／Figma 對照才准 merge。

**要做**：
1. 定義「UI 專案」判定與視覺優先閘門：進碼前需有 Figma 定稿或臨時網頁，經 Chuan 美學確認。
2. 用 Figma MCP／figma skills 建立 design→code 的 tokens/context 拉取流程。
3. 把「UI PR 需附視覺對照」塞進 ① 的 merge 綠燈條件。

**Acceptance**：一個 UI 專案能走完「Figma 定稿→確認→實作→UI PR 附對照→綠燈 merge」；Figma 與碼的漂移在 PR 時被檢出。

---

## 未來（非本輪）
- canvas 演化成活文件：加「各專案 × 採用了哪些 skill」的採用矩陣層。
- 對齊 `workflow.md` 與實際 skills（已 drift：feature/health-audit/handoff-prompt/apply-coding-rules/gh-fix 未列；claude-md-improver 已不存在）。
