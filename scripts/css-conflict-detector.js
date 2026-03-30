#!/usr/bin/env node

/**
 * CSS衝突檢測工具
 * 用於檢測 mobile-optimization.css 與 style.css 之間的衝突
 * 
 * 使用方法：
 * node scripts/css-conflict-detector.js
 */

const fs = require('fs');
const path = require('path');

// 配置文件路徑
const STYLE_CSS_PATH = path.join(__dirname, '../static/css/style.css');
const MOBILE_CSS_PATH = path.join(__dirname, '../static/css/mobile-optimization.css');
const OUTPUT_PATH = path.join(__dirname, '../docs/css-conflict-report.md');

// 解析CSS文件，提取選擇器和屬性
function parseCSS(filePath) {
    if (!fs.existsSync(filePath)) {
        console.error(`文件不存在: ${filePath}`);
        return { selectors: {}, mediaQueries: {} };
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    const selectors = {};
    const mediaQueries = {};
    
    // 移除註釋
    let cleanedContent = content.replace(/\/\*[\s\S]*?\*\//g, '');
    
    // 提取媒體查詢
    const mediaQueryRegex = /@media[^{]+\{([\s\S]*?})\s*}/g;
    let mediaMatch;
    while ((mediaMatch = mediaQueryRegex.exec(cleanedContent)) !== null) {
        const mediaContent = mediaMatch[1];
        const mediaKey = mediaMatch[0].match(/@media[^{]+/)[0].trim();
        mediaQueries[mediaKey] = parseCSSContent(mediaContent);
    }
    
    // 移除媒體查詢內容
    cleanedContent = cleanedContent.replace(/@media[^{]+\{[\s\S]*?}\s*}/g, '');
    
    // 解析剩餘內容
    Object.assign(selectors, parseCSSContent(cleanedContent));
    
    return { selectors, mediaQueries };
}

function parseCSSContent(content) {
    const selectors = {};
    const selectorRegex = /([^{]+)\{([^}]+)\}/g;
    let match;
    
    while ((match = selectorRegex.exec(content)) !== null) {
        const selector = match[1].trim();
        const properties = match[2].trim();
        
        // 分割屬性
        const propList = properties.split(';').filter(p => p.trim());
        const propMap = {};
        
        propList.forEach(prop => {
            const [key, value] = prop.split(':').map(s => s.trim());
            if (key && value) {
                propMap[key] = value;
            }
        });
        
        if (Object.keys(propMap).length > 0) {
            selectors[selector] = propMap;
        }
    }
    
    return selectors;
}

// 檢測衝突
function detectConflicts(styleData, mobileData) {
    const conflicts = {
        selectorConflicts: [],
        propertyConflicts: [],
        mediaQueryConflicts: [],
        duplicateSelectors: []
    };
    
    // 檢測選擇器衝突
    const styleSelectors = Object.keys(styleData.selectors);
    const mobileSelectors = Object.keys(mobileData.selectors);
    
    // 重複的選擇器
    const duplicateSelectors = styleSelectors.filter(selector => 
        mobileSelectors.includes(selector)
    );
    
    conflicts.duplicateSelectors = duplicateSelectors;
    
    // 屬性衝突
    duplicateSelectors.forEach(selector => {
        const styleProps = styleData.selectors[selector];
        const mobileProps = mobileData.selectors[selector];
        
        const commonProps = Object.keys(styleProps).filter(prop => 
            mobileProps.hasOwnProperty(prop)
        );
        
        commonProps.forEach(prop => {
            if (styleProps[prop] !== mobileProps[prop]) {
                conflicts.propertyConflicts.push({
                    selector,
                    property: prop,
                    styleValue: styleProps[prop],
                    mobileValue: mobileProps[prop]
                });
            }
        });
    });
    
    // 媒體查詢衝突
    const styleMedia = Object.keys(styleData.mediaQueries);
    const mobileMedia = Object.keys(mobileData.mediaQueries);
    
    const commonMedia = styleMedia.filter(media => 
        mobileMedia.includes(media)
    );
    
    commonMedia.forEach(media => {
        const styleMediaSelectors = Object.keys(styleData.mediaQueries[media]);
        const mobileMediaSelectors = Object.keys(mobileData.mediaQueries[media]);
        
        const duplicateMediaSelectors = styleMediaSelectors.filter(selector => 
            mobileMediaSelectors.includes(selector)
        );
        
        if (duplicateMediaSelectors.length > 0) {
            conflicts.mediaQueryConflicts.push({
                mediaQuery: media,
                duplicateSelectors: duplicateMediaSelectors
            });
        }
    });
    
    return conflicts;
}

// 生成報告
function generateReport(conflicts, styleData, mobileData) {
    let report = `# CSS衝突檢測報告\n\n`;
    report += `**生成時間**: ${new Date().toLocaleString()}\n`;
    report += `**檢測文件**:\n`;
    report += `- style.css: ${Object.keys(styleData.selectors).length} 個選擇器\n`;
    report += `- mobile-optimization.css: ${Object.keys(mobileData.selectors).length} 個選擇器\n\n`;
    
    report += `## 📊 衝突統計\n\n`;
    report += `| 衝突類型 | 數量 |\n`;
    report += `|----------|------|\n`;
    report += `| 重複選擇器 | ${conflicts.duplicateSelectors.length} |\n`;
    report += `| 屬性衝突 | ${conflicts.propertyConflicts.length} |\n`;
    report += `| 媒體查詢衝突 | ${conflicts.mediaQueryConflicts.length} |\n\n`;
    
    if (conflicts.duplicateSelectors.length > 0) {
        report += `## 🔍 重複選擇器\n\n`;
        conflicts.duplicateSelectors.forEach((selector, index) => {
            report += `${index + 1}. \`${selector}\`\n`;
        });
        report += `\n`;
    }
    
    if (conflicts.propertyConflicts.length > 0) {
        report += `## ⚠️ 屬性衝突\n\n`;
        report += `| 選擇器 | 屬性 | style.css 值 | mobile-optimization.css 值 |\n`;
        report += `|--------|------|--------------|----------------------------|\n`;
        
        conflicts.propertyConflicts.forEach(conflict => {
            report += `| \`${conflict.selector}\` | \`${conflict.property}\` | \`${conflict.styleValue}\` | \`${conflict.mobileValue}\` |\n`;
        });
        report += `\n`;
    }
    
    if (conflicts.mediaQueryConflicts.length > 0) {
        report += `## 📱 媒體查詢衝突\n\n`;
        conflicts.mediaQueryConflicts.forEach(conflict => {
            report += `### ${conflict.mediaQuery}\n\n`;
            report += `重複選擇器:\n`;
            conflict.duplicateSelectors.forEach(selector => {
                report += `- \`${selector}\`\n`;
            });
            report += `\n`;
        });
    }
    
    // 添加建議
    report += `## 💡 修復建議\n\n`;
    
    if (conflicts.propertyConflicts.length > 0) {
        report += `### 1. 屬性衝突修復\n\n`;
        report += `對於屬性衝突，建議：\n\n`;
        report += `1. **優先使用 style.css 的值**，因為它是主樣式文件\n`;
        report += `2. **在 mobile-optimization.css 中使用更高特異性**，例如：\n`;
        report += `   \`\`\`css\n`;
        report += `   /* 錯誤：直接覆蓋 */\n`;
        report += `   .btn { padding: 10px; }\n`;
        report += `   \n`;
        report += `   /* 正確：使用更高特異性 */\n`;
        report += `   body.mobile-optimized .btn { padding: 10px; }\n`;
        report += `   \`\`\`\n\n`;
    }
    
    if (conflicts.mediaQueryConflicts.length > 0) {
        report += `### 2. 媒體查詢衝突修復\n\n`;
        report += `建議統一媒體查詢斷點：\n\n`;
        report += `1. **標準化斷點**：\n`;
        report += `   - 手機: \`@media (max-width: 767.98px)\`\n`;
        report += `   - 平板: \`@media (min-width: 768px) and (max-width: 991.98px)\`\n`;
        report += `   - 桌面: \`@media (min-width: 992px)\`\n\n`;
        report += `2. **合併重複的媒體查詢**\n\n`;
    }
    
    report += `### 3. 整體架構建議\n\n`;
    report += `1. **創建新的移動端增強文件** (\`mobile-enhanced.css\`)\n`;
    report += `2. **使用條件加載**：只在移動設備加載\n`;
    report += `3. **採用漸進式增強**：只添加移動端特定樣式\n`;
    report += `4. **建立CSS變量系統**：統一顏色、間距等設計令牌\n\n`;
    
    report += `## 🚀 實施步驟\n\n`;
    report += `1. **備份現有文件**\n`;
    report += `2. **修復最嚴重的屬性衝突**（前10個）\n`;
    report += `3. **創建 mobile-enhanced.css 框架**\n`;
    report += `4. **逐步遷移 mobile-optimization.css 中的樣式**\n`;
    report += `5. **測試和驗證**\n\n`;
    
    return report;
}

// 主函數
function main() {
    console.log('🔍 開始CSS衝突檢測...\n');
    
    // 解析CSS文件
    console.log('📄 解析 style.css...');
    const styleData = parseCSS(STYLE_CSS_PATH);
    console.log(`   找到 ${Object.keys(styleData.selectors).length} 個選擇器\n`);
    
    console.log('📄 解析 mobile-optimization.css...');
    const mobileData = parseCSS(MOBILE_CSS_PATH);
    console.log(`   找到 ${Object.keys(mobileData.selectors).length} 個選擇器\n`);
    
    // 檢測衝突
    console.log('⚡ 檢測衝突...');
    const conflicts = detectConflicts(styleData, mobileData);
    
    // 生成報告
    console.log('📊 生成報告...');
    const report = generateReport(conflicts, styleData, mobileData);
    
    // 保存報告
    fs.writeFileSync(OUTPUT_PATH, report, 'utf8');
    console.log(`✅ 報告已保存到: ${OUTPUT_PATH}\n`);
    
    // 輸出摘要
    console.log('📈 衝突摘要:');
    console.log(`   重複選擇器: ${conflicts.duplicateSelectors.length}`);
    console.log(`   屬性衝突: ${conflicts.propertyConflicts.length}`);
    console.log(`   媒體查詢衝突: ${conflicts.mediaQueryConflicts.length}\n`);
    
    if (conflicts.propertyConflicts.length > 0) {
        console.log('⚠️  發現屬性衝突，建議優先修復以下問題:');
        conflicts.propertyConflicts.slice(0, 5).forEach((conflict, index) => {
            console.log(`   ${index + 1}. ${conflict.selector} 的 ${conflict.property} 屬性`);
            console.log(`      style.css: ${conflict.styleValue}`);
            console.log(`      mobile-optimization.css: ${conflict.mobileValue}\n`);
        });
    }
    
    console.log('🎯 建議查看完整報告獲取詳細信息和修復建議。');
}

// 執行
if (require.main === module) {
    try {
        main();
    } catch (error) {
        console.error('❌ 檢測過程中發生錯誤:', error.message);
        process.exit(1);
    }
}

module.exports = { parseCSS, detectConflicts, generateReport };