# 可视化报告生成指南

报告为**单文件 HTML**（内联样式 + Chart.js），数据源是阶段 1/2 的采集输出。模板见 `assets/report_template.html`：把采集数据填进模板的 `REPORT` 数据区即可，无需从零写结构。

## 产出方式

- 环境提供内联展示能力（如内联 widget 工具）→ 内联展示报告；
- 否则把 HTML 落盘到 `<产物目录>`（默认 `<项目根>/.tasks/nas-report-<日期>.html`，过程产物不入库）并提示用户用浏览器打开；
- Chart.js 从 CDN 加载（`cdnjs.cloudflare.com` 的 UMD 版本）；无外网的离线环境改成本地文件或去掉图表只留表格。

## 报告结构

### 1. 顶部指标卡片

4 格网格，展示核心数字：在线硬盘数、故障硬盘数、降级阵列数、数据安全状态。

```html
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;">
  <div style="background: #F5F7FA; border-radius: 8px; padding: 12px;">
    <p style="font-size: 11px; color: #666; margin: 0 0 4px 0;">在线硬盘</p>
    <p style="font-size: 22px; font-weight: 500; margin: 0; color: #1D9E75;">7 / 8</p>
  </div>
  <!-- 故障硬盘 / 降级阵列 / 数据安全 -->
</div>
```

### 2. 硬盘槽位状态网格

按实际盘位数出网格，每格用颜色标识状态：

- 绿色 `#E1F5EE` + 边框 `#5DCAA5`：健康
- 黄色 `#FAEEDA` + 边框 `#FAC775`：需关注
- 红色 `#FCEBEB` + 边框 `#E24B4A`：故障
- 蓝色 `#E6F1FB` + 边框 `#85B7EB`：系统盘

每格包含：盘位号、容量/类型、RAID 状态。

### 3. SMART 关键指标柱状图

水平柱状图，**对数刻度**（数值跨度大，坏扇区可从 0 到数万）：

```javascript
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['已重映射扇区\n(ID=5)', '待处理坏扇区\n(ID=197)', '离线不可纠正\n(ID=198)'],
    datasets: [{
      data: [4616, 33976, 33976],
      backgroundColor: ['#EF9F27', '#E24B4A', '#E24B4A']
    }]
  },
  options: { indexAxis: 'y', scales: { x: { type: 'logarithmic' } } }
});
```

颜色规则：

- `#E24B4A`（红）：危险指标（197 / 198 / 187 / 188 严重超标）
- `#EF9F27`（黄）：警告指标（5 / 199 轻微超标）

### 4. 通电时间对比图

所有硬盘的 Power_On_Hours 对比，颜色按健康状态：

```javascript
const colors = disks.map(d => d.status === 'faulty' ? '#E24B4A'
                        : (d.status === 'warning' ? '#FAC775' : '#5DCAA5'));
```

Tooltip 显示年数换算：`hours.toLocaleString() + ' 小时 (约 ' + (hours / 8760).toFixed(1) + ' 年)'`

### 5. 详细参数表格

每块硬盘一个卡片，双列布局展示完整参数。**品牌必须包含中文名**（对照表见 `SKILL.md`）：

```html
<tr>
  <td style="color: #0F6E56; width: 90px;">品牌</td>
  <td>HGST 昱科（原日立，现属西部数据）</td>
</tr>
```

## 配色规范

| 用途 | 背景色 | 边框色 | 文字色 |
|------|--------|--------|--------|
| 健康 | #E1F5EE | #5DCAA5 | #085041 |
| 关注 | #FAEEDA | #FAC775 | #633806 |
| 故障 | #FCEBEB | #E24B4A | #791F1F |
| 系统盘 | #E6F1FB | #85B7EB | #042C53 |

## 技术约束

1. Chart.js 用 CDN 的 UMD 版本；canvas 必须有 `role="img"` 与 `aria-label`。
2. 浅色主题（适配 IDE）；字体不小于 11px。
3. 不使用 emoji，用 CSS 形状或文字符号代替。
4. 报告中**不含连接凭据**（地址中的账号 / 密码一律不写），只含设备与健康数据。
5. 报告中的盘位、容量、故障数必须与采集输出逐项一致，不做推算或补全。
