#!/bin/bash
# 安全检查脚本 - 确保没有敏感信息被提交到Git

echo "🔍 正在检查 step2-data2DB 目录的安全性..."

# 检查是否存在 .gitignore 文件
if [ ! -f ".gitignore" ]; then
    echo "❌ 缺少 .gitignore 文件！"
    exit 1
else
    echo "✅ .gitignore 文件存在"
fi

# 检查是否有 config.env 文件被 git 跟踪
echo "🔍 检查 config.env 文件是否被正确忽略..."

tracked_config_files=$(git ls-files | grep "config\.env$" 2>/dev/null)
if [ -n "$tracked_config_files" ]; then
    echo "❌ 发现被跟踪的 config.env 文件："
    echo "$tracked_config_files"
    echo "请运行: git rm --cached <file> 来移除这些文件"
    exit 1
else
    echo "✅ 没有 config.env 文件被 git 跟踪"
fi

# 检查暂存区中是否有敏感文件
echo "🔍 检查暂存区..."
staged_sensitive=$(git diff --cached --name-only | grep -E "\.(env|key|pem|p12)$|config\.env" 2>/dev/null)
if [ -n "$staged_sensitive" ]; then
    echo "❌ 暂存区中发现敏感文件："
    echo "$staged_sensitive"
    echo "请运行: git reset HEAD <file> 来取消暂存"
    exit 1
else
    echo "✅ 暂存区中没有敏感文件"
fi

# 检查是否有硬编码的密钥（基本检查）
echo "🔍 检查硬编码密钥..."
hardcoded_patterns="(SUPABASE_KEY|DATABASE_URL|API_KEY|SECRET|PASSWORD)\s*=\s*[\"'][^\"']*[\"']"

if grep -r -E "$hardcoded_patterns" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v "config\.env" | grep -v "\.example" | grep -v "your_" | grep -v "YOUR_"; then
    echo "❌ 发现可能的硬编码密钥！请检查上述文件"
    exit 1
else
    echo "✅ 没有发现明显的硬编码密钥"
fi

# 检查 config.env.example 是否存在且不包含真实密钥
echo "🔍 检查配置模板文件..."
for dir in . product-main-table review-tables product-review-meta-categorization; do
    if [ -d "$dir" ]; then
        config_example="$dir/config.env.example"
        if [ -f "$config_example" ]; then
            if grep -q "your_.*_here\|YOUR_.*_HERE\|eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" "$config_example"; then
                echo "✅ $config_example 看起来是安全的模板"
            else
                echo "⚠️  $config_example 可能包含真实密钥，请检查"
            fi
        else
            echo "⚠️  缺少 $config_example 模板文件"
        fi
    fi
done

echo ""
echo "🎉 安全检查完成！"
echo ""
echo "📋 提交前检查清单："
echo "  - [ ] 运行了 ./check_security.sh"
echo "  - [ ] 所有检查都通过"
echo "  - [ ] git status 显示没有敏感文件"
echo "  - [ ] 代码中没有硬编码密钥"
echo ""
echo "如果所有检查都通过，可以安全地提交代码。" 