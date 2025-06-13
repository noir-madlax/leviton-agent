# 产品市场分析图表代码示例

## 基于Step4维度的图表生成示例

### 维度1：客户痛点分析 - 痛点严重程度与评论量分析

```json
{
  "chart1": {
    "code": "const painPointData = [\n  { category: '安装困难', reviewCount: 45, severity: 4.2, affectedCustomers: 180 },\n  { category: '产品耐用性', reviewCount: 38, severity: 4.8, affectedCustomers: 150 },\n  { category: '用户体验', reviewCount: 67, severity: 3.5, affectedCustomers: 280 },\n  { category: '性能参数', reviewCount: 23, severity: 4.0, affectedCustomers: 90 },\n  { category: '外观设计', reviewCount: 15, severity: 2.8, affectedCustomers: 60 }\n];\n\nconst DynamicChart = () => {\n  return (\n    <ResponsiveContainer width=\"100%\" height={400}>\n      <ScatterChart data={painPointData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>\n        <CartesianGrid strokeDasharray=\"3 3\" />\n        <XAxis \n          dataKey=\"reviewCount\" \n          name=\"评论数量\"\n          label={{ value: '评论数量', position: 'insideBottom', offset: -10 }}\n        />\n        <YAxis \n          dataKey=\"severity\"\n          name=\"严重程度\"\n          domain={[1, 5]}\n          label={{ value: '严重程度评分', angle: -90, position: 'insideLeft' }}\n        />\n        <Tooltip \n          formatter={(value, name) => {\n            if (name === 'affectedCustomers') return [`${value}人`, '影响客户数'];\n            if (name === 'severity') return [`${value}分`, '严重程度'];\n            if (name === 'reviewCount') return [`${value}条`, '评论数量'];\n            return [value, name];\n          }}\n          labelFormatter={(label) => `痛点类别: ${label}`}\n        />\n        <Legend verticalAlign=\"top\" height={36} />\n        <Scatter \n          dataKey=\"severity\" \n          fill=\"#ff6b6b\"\n          name=\"严重程度评分\"\n        >\n          {painPointData.map((entry, index) => (\n            <Cell key={`cell-${index}`} \n              fill={entry.severity > 4 ? '#ff4757' : entry.severity > 3 ? '#ffa502' : '#7bed9f'} \n            />\n          ))}\n        </Scatter>\n      </ScatterChart>\n    </ResponsiveContainer>\n  );\n};",
    "explanation": "该散点图展示了客户痛点的严重程度与评论数量的关系。X轴表示每个痛点的评论数量，Y轴表示严重程度评分(1-5分)，点的颜色表示严重程度级别：红色(高严重度>4分)、橙色(中等严重度3-4分)、绿色(低严重度<3分)。",
    "insights": "从图表可以看出：用户体验问题虽然严重程度中等(3.5分)，但评论数量最多(67条)，影响客户最广泛，需要优先关注。产品耐用性问题严重程度最高(4.8分)且评论数量较多，是最需要立即解决的核心痛点。安装困难也是高严重度问题，建议改进安装指导或设计。"
  },
  "chart2": {
    "code": "const marketGapData = [\n  { opportunity: '智能控制功能', demandIntensity: 85, gapLevel: 4.2, marketValue: 95 },\n  { opportunity: '能耗优化', demandIntensity: 72, gapLevel: 3.8, marketValue: 80 },\n  { opportunity: '多场景适配', demandIntensity: 68, gapLevel: 4.5, marketValue: 75 },\n  { opportunity: '简化安装', demandIntensity: 90, gapLevel: 3.2, marketValue: 88 },\n  { opportunity: '耐用性提升', demandIntensity: 78, gapLevel: 4.8, marketValue: 92 },\n  { opportunity: '美观设计', demandIntensity: 45, gapLevel: 2.8, marketValue: 35 },\n  { opportunity: '价格竞争力', demandIntensity: 95, gapLevel: 3.5, marketValue: 70 }\n];\n\nconst DynamicChart = () => {\n  return (\n    <ResponsiveContainer width=\"100%\" height={400}>\n      <ScatterChart data={marketGapData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>\n        <CartesianGrid strokeDasharray=\"3 3\" />\n        <XAxis \n          dataKey=\"demandIntensity\" \n          name=\"市场需求强度\"\n          domain={[0, 100]}\n          label={{ value: '市场需求强度', position: 'insideBottom', offset: -10 }}\n        />\n        <YAxis \n          dataKey=\"gapLevel\"\n          name=\"解决方案缺口\"\n          domain={[1, 5]}\n          label={{ value: '解决方案缺口程度', angle: -90, position: 'insideLeft' }}\n        />\n        <Tooltip \n          cursor={{ strokeDasharray: '3 3' }}\n          formatter={(value, name) => {\n            if (name === 'marketValue') return [`${value}%`, '市场价值'];\n            if (name === 'gapLevel') return [`${value}分`, '缺口程度'];\n            if (name === 'demandIntensity') return [`${value}分`, '需求强度'];\n            return [value, name];\n          }}\n          labelFormatter={(label) => `机会点: ${label}`}\n        />\n        <Legend verticalAlign=\"top\" height={36} />\n        <Scatter dataKey=\"gapLevel\" fill=\"#3742fa\" name=\"解决方案缺口程度\">\n          {marketGapData.map((entry, index) => (\n            <Cell \n              key={`cell-${index}`} \n              fill={entry.marketValue > 80 ? '#2ed573' : entry.marketValue > 60 ? '#ffa502' : '#ff6348'}\n            />\n          ))}\n        </Scatter>\n      </ScatterChart>\n    </ResponsiveContainer>\n  );\n};",
    "explanation": "该市场机会优先级矩阵展示了不同优化机会的市场需求强度与当前解决方案缺口的关系。X轴表示市场需求强度(0-100分)，Y轴表示当前解决方案缺口程度(1-5分)，气泡颜色表示潜在市场价值：绿色(高价值>80%)、橙色(中等价值60-80%)、红色(低价值<60%)。",
    "insights": "右上角的高价值机会点最值得投资：多场景适配(需求68分，缺口4.5分)和耐用性提升(需求78分，缺口4.8分)是最有潜力的优化方向。价格竞争力虽然需求最高(95分)，但缺口适中且市场价值相对较低，可能竞争激烈。简化安装需求很高但缺口较小，说明市场已有较好解决方案。"
  }
}
```

### 维度2：竞争优势分析 - 特性优势与竞争对比

```json
{
  "chart1": {
    "code": "const featureData = [\n  { feature: '智能控制', mentions: 125, satisfaction: 4.3 },\n  { feature: '外观设计', mentions: 89, satisfaction: 4.1 },\n  { feature: '安装便捷', mentions: 67, satisfaction: 3.8 },\n  { feature: '性能稳定', mentions: 156, satisfaction: 4.5 },\n  { feature: '价格优势', mentions: 203, satisfaction: 4.0 },\n  { feature: '售后服务', mentions: 45, satisfaction: 3.9 },\n  { feature: '创新功能', mentions: 78, satisfaction: 4.2 }\n];\n\nconst DynamicChart = () => {\n  return (\n    <ResponsiveContainer width=\"100%\" height={400}>\n      <BarChart data={featureData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>\n        <CartesianGrid strokeDasharray=\"3 3\" />\n        <XAxis \n          dataKey=\"feature\" \n          angle={-45}\n          textAnchor=\"end\"\n          height={80}\n        />\n        <YAxis yAxisId=\"left\" orientation=\"left\" />\n        <YAxis yAxisId=\"right\" orientation=\"right\" domain={[3, 5]} />\n        <Tooltip \n          formatter={(value, name) => {\n            if (name === '提及次数') return [`${value}次`, name];\n            if (name === '满意度评分') return [`${value}分`, name];\n            return [value, name];\n          }}\n        />\n        <Legend verticalAlign=\"top\" height={36} />\n        <Bar yAxisId=\"left\" dataKey=\"mentions\" fill=\"#8884d8\" name=\"提及次数\" />\n        <Bar yAxisId=\"right\" dataKey=\"satisfaction\" fill=\"#82ca9d\" name=\"满意度评分\" />\n      </BarChart>\n    </ResponsiveContainer>\n  );\n};",
    "explanation": "该组合柱状图展示了产品各项特性的用户关注度(提及次数)和满意度评分。左侧Y轴显示提及次数，右侧Y轴显示满意度评分(3-5分范围)，可以同时观察哪些特性最受关注且满意度最高。",
    "insights": "性能稳定是最大的竞争优势，既有最高的满意度(4.5分)又有很高的关注度(156次提及)。价格优势关注度最高(203次)但满意度一般(4.0分)，说明虽然有价格竞争力但仍有提升空间。智能控制和创新功能满意度较高，可作为差异化卖点重点宣传。"
  },
  "chart2": {
    "code": "const competitiveData = [\n  { dimension: '性能表现', ourProduct: 4.2, competitorA: 3.8, competitorB: 4.0, competitorC: 3.5 },\n  { dimension: '外观设计', ourProduct: 4.0, competitorA: 4.3, competitorB: 3.7, competitorC: 4.1 },\n  { dimension: '操作便捷', ourProduct: 4.1, competitorA: 3.9, competitorB: 4.2, competitorC: 3.8 },\n  { dimension: '价格竞争力', ourProduct: 3.8, competitorA: 4.1, competitorB: 3.6, competitorC: 4.0 },\n  { dimension: '售后服务', ourProduct: 4.3, competitorA: 3.7, competitorB: 3.9, competitorC: 3.6 },\n  { dimension: '创新特性', ourProduct: 4.4, competitorA: 3.5, competitorB: 3.8, competitorC: 3.2 }\n];\n\nconst DynamicChart = () => {\n  return (\n    <ResponsiveContainer width=\"100%\" height={400}>\n      <LineChart data={competitiveData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>\n        <CartesianGrid strokeDasharray=\"3 3\" />\n        <XAxis \n          dataKey=\"dimension\" \n          angle={-45}\n          textAnchor=\"end\"\n          height={80}\n        />\n        <YAxis domain={[3, 5]} />\n        <Tooltip formatter={(value) => [`${value}分`, '评分']} />\n        <Legend verticalAlign=\"top\" height={36} />\n        <Line type=\"monotone\" dataKey=\"ourProduct\" stroke=\"#2ed573\" strokeWidth={3} name=\"我们的产品\" />\n        <Line type=\"monotone\" dataKey=\"competitorA\" stroke=\"#ff6b6b\" strokeWidth={2} name=\"竞争对手A\" />\n        <Line type=\"monotone\" dataKey=\"competitorB\" stroke=\"#4834d4\" strokeWidth={2} name=\"竞争对手B\" />\n        <Line type=\"monotone\" dataKey=\"competitorC\" stroke=\"#ffa502\" strokeWidth={2} name=\"竞争对手C\" />\n      </LineChart>\n    </ResponsiveContainer>\n  );\n};",
    "explanation": "该雷达式折线图对比了我们的产品与3个主要竞争对手在6个关键维度上的表现。每条线代表一个产品，数值越高表示在该维度上表现越好(评分范围3-5分)。",
    "insights": "我们的产品在创新特性(4.4分)、售后服务(4.3分)和性能表现(4.2分)方面具有明显优势，这些是核心竞争力。但在外观设计和价格竞争力方面存在劣势，特别是价格竞争力(3.8分)低于多数竞争对手。建议保持技术和服务优势的同时，重点改进设计美感和成本控制。"
  }
}
```

## JSON输出格式说明

### 单图表格式 (现有格式)
```json
{
  "chartData": {
    "code": "React组件代码字符串",
    "explanation": "图表说明",
    "insights": "数据洞察"
  }
}
```

### 多图表格式 (新增支持)
```json
{
  "chart1": {
    "code": "第一个图表的React组件代码",
    "explanation": "第一个图表的说明",
    "insights": "第一个图表的洞察"
  },
  "chart2": {
    "code": "第二个图表的React组件代码", 
    "explanation": "第二个图表的说明",
    "insights": "第二个图表的洞察"
  }
}
```

## 图表类型建议

### 痛点分析维度
- **散点图 (ScatterChart)**: 适合展示痛点严重程度与影响范围的关系
- **堆叠柱状图 (StackedBarChart)**: 适合展示不同类别痛点的分布
- **热力图效果**: 使用颜色编码表示严重程度

### 市场机会分析维度  
- **气泡图 (BubbleChart)**: 适合展示需求强度、解决方案缺口和市场价值的三维关系
- **矩阵散点图**: 适合优先级分析和机会识别

### 竞争优势分析维度
- **雷达图效果的折线图**: 适合多维度竞争对比
- **组合柱状图**: 适合展示关注度和满意度的双重指标
- **水平柱状图**: 适合排序展示优势特性

## 代码规范要求

1. **必须使用的组件名**: `DynamicChart`
2. **必须包装**: `ResponsiveContainer`
3. **禁止使用**: import/export语句
4. **数据硬编码**: 所有数据直接定义在组件内
5. **颜色方案**: 使用语义化颜色(红色=严重/劣势, 绿色=良好/优势, 橙色=中等)
6. **交互支持**: 包含Tooltip和Legend组件

## 布局优化要求（防止重叠）

1. **外边距设置**: 所有图表必须使用 `margin={{ top: 50, right: 30, left: 40, bottom: 80 }}`
2. **图例位置**: 优先使用 `verticalAlign="top" height={36}` 置于图表顶部
3. **X轴标签**: 当标签文字较长时，使用 `angle={-45} textAnchor="end" height={80}`
4. **Y轴标签**: 使用 `angle={-90}` 并增加左边距到40px
5. **饼图特殊处理**: 设置 `cy="45%"` 并减小 `outerRadius` 为100px
6. **散点图气泡**: 控制气泡大小避免超出图表区域 