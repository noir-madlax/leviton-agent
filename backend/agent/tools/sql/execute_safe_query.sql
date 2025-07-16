-- 创建安全查询执行函数
-- 此函数只允许 SELECT 查询，用于 BI 分析工具
CREATE OR REPLACE FUNCTION execute_safe_query(query_text TEXT)
RETURNS TABLE(result JSONB)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    cleaned_query TEXT;
    dangerous_keywords TEXT[] := ARRAY[
        'insert', 'update', 'delete', 'drop', 'create', 'alter', 
        'truncate', 'replace', 'merge', 'grant', 'revoke',
        'exec', 'execute', 'call', 'declare', 'set',
        'begin', 'commit', 'rollback', 'savepoint',
        'copy', 'bulk', 'load', 'import', 'export'
    ];
    keyword TEXT;
BEGIN
    -- 清理查询文本
    cleaned_query := TRIM(LOWER(query_text));
    
    -- 检查是否为空
    IF cleaned_query = '' OR cleaned_query IS NULL THEN
        RAISE EXCEPTION 'Query cannot be empty';
    END IF;
    
    -- 检查是否以 SELECT 开头
    IF NOT cleaned_query LIKE 'select%' THEN
        RAISE EXCEPTION 'Only SELECT queries are allowed';
    END IF;
    
    -- 检查危险关键词
    FOREACH keyword IN ARRAY dangerous_keywords
    LOOP
        IF cleaned_query ~ ('\y' || keyword || '\y') THEN
            RAISE EXCEPTION 'Dangerous keyword detected: %', keyword;
        END IF;
    END LOOP;
    
    -- 检查多语句（分号后还有内容）
    IF query_text ~ ';.+' THEN
        RAISE EXCEPTION 'Multiple statements are not allowed';
    END IF;
    
    -- 执行查询并返回 JSON 结果
    RETURN QUERY
    EXECUTE format('SELECT to_jsonb(t) FROM (%s) t', query_text);
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Query execution failed: %', SQLERRM;
END;
$$;

-- 为函数添加注释
COMMENT ON FUNCTION execute_safe_query(TEXT) IS 'Executes safe SELECT queries and returns results as JSONB. Only allows SELECT statements for BI analysis.';