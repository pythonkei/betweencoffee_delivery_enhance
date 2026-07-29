#!/bin/bash
# verify-css-usage.sh — CSS 檔案引用驗證腳本
# 用法: bash scripts/verify-css-usage.sh
# 功能: 掃描所有檔案，確認每個 CSS 檔案的真實引用來源

PROJECT_DIR="/home/kei/Desktop/betweencoffee_delivery_enhance"
OUTPUT_FILE="${PROJECT_DIR}/scripts/css-usage-report.txt"

echo "============================================" > "$OUTPUT_FILE"
echo "CSS 檔案引用分析報告" >> "$OUTPUT_FILE"
echo "生成時間: $(date)" >> "$OUTPUT_FILE"
echo "============================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 要檢查的可疑檔案清單
SUSPECT_FILES=(
  "temp.css"
  "blobs.css"
  "core.css"
  "module.css"
  "animate.css"
  "owl.carousel.min.css"
  "owl.theme.default.min.css"
  "magnific-popup.css"
  "aos.css"
  "flaticon.css"
  "ionicons.min.css"
  "jquery.timepicker.min.css"
  "select2.min.css"
  "open-iconic-bootstrap.min.css"
  "bootstrap-datepicker.css"
  "colorbox.css"
  "_jquery.timepicker.css"
)

echo "=== 搜尋所有 HTML/PY/JS 檔案中的 CSS 引用 ===" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for css_file in "${SUSPECT_FILES[@]}"; do
  # 排除 node_modules, .git, migrations, venv
  RESULTS=$(grep -r --include="*.html" --include="*.py" --include="*.js" --include="*.txt" \
    -l "$css_file" "$PROJECT_DIR/" \
    2>/dev/null | grep -v "node_modules\|\.git\|migrations\|venv\|\.venv\|cdnjs\|static/css\|static/fonts" || echo "")
  
  LINE_COUNT=$(wc -l < "$PROJECT_DIR/static/css/$css_file" 2>/dev/null || echo "0")
  
  if [ -z "$RESULTS" ]; then
    RESULTS="(無引用)"
    echo "❌ $css_file (${LINE_COUNT}行) → 未在任何模板/JS 中被引用" >> "$OUTPUT_FILE"
  else
    echo "✅ $css_file (${LINE_COUNT}行) → 被引用於:" >> "$OUTPUT_FILE"
    echo "$RESULTS" | sed 's/^/    - /' >> "$OUTPUT_FILE"
  fi
  echo "" >> "$OUTPUT_FILE"
done

echo "" >> "$OUTPUT_FILE"
echo "=== base.html 載入的所有 CSS 檔案清單 ===" >> "$OUTPUT_FILE"
grep -i "static.*css" "$PROJECT_DIR/templates/betweencoffee_delivery/base.html" | \
  sed 's/.*static.//;s/".*//' >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "=== dist-aggressive 目錄內容（PurgeCSS 輸出）===" >> "$OUTPUT_FILE"
ls -la "$PROJECT_DIR/static/css/dist-aggressive/" 2>/dev/null >> "$OUTPUT_FILE" || echo "(目錄不存在或空)" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "============================================" >> "$OUTPUT_FILE"
echo "報告已保存: $OUTPUT_FILE"
echo "============================================"

# 顯示摘要
echo ""
echo "========== 摘要 =========="
echo "❌ = 未在任何地方引用，可安全刪除"
echo "✅ = 仍有引用，不可刪除"