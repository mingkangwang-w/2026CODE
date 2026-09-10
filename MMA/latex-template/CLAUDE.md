# CUMCM-Latex-template

数学建模国赛（CUMCM）LaTeX模板，适用于中国大学生数学建模竞赛论文撰写，支持中文、公式、代码、参考文献、自动目录等。


## 项目结构

- `document.tex`：主控文件，包含所有章节和宏包设置。
- `cumcmthesis.cls`：模板核心类文件，定义论文格式。
- `book.bib`：参考文献数据库（BibTeX格式）。
- `code/`：存放代码示例（支持Python、MATLAB等）。
- `texfile/`：各章节内容，按比赛论文结构拆分：
  - `1abstract.tex`：摘要
  - `2ProblemRestatement.tex`：问题重述
  - `3ProblemAnalysis.tex`：问题分析
  - `4AssumptionAndSign.tex`：假设与符号说明
  - `5MakeModel.tex`：模型建立与求解
  - `6ErrorAnalysis.tex`：误差分析
  - `7ModelEvaluation.tex`：模型评价
  - `8Reference.tex`：参考文献
  - `9Appendix.tex`：附录
  - `figures/`：图片资源
- `常用LaTex代码指令.txt`：常用LaTeX命令备忘
- `clean.bat`；冗余文件批处理脚本

## 主要功能

- 支持中文排版（ctex）
- 自动生成目录、图表目录
- 参考文献自动排序与压缩（natbib、bibtex）
- 代码高亮（listings）
- 数学公式增强（amsmath、amssymb）
- 页面布局灵活（geometry）
- 支持多栏、长表格、旋转图表等
- PDF跳转与超链接（hyperref）


## 使用方法

1. 使用 XeLaTeX 编译 `document.tex`，可自动生成 PDF。
   ```bash
   latexmk -xelatex -interaction=nonstopmode document.tex
   ```
2. 按需编辑 `texfile/` 下各章节内容，图片放入 `texfile/figures/` 文件夹。
3. 参考文献统一使用 BibTeX：编辑 `book.bib`，正文引用格式如 `\cite{引用标签}`，输出样式在 `texfile/8Reference.tex` 中设置为 `gbt7714-numerical`。
4. 代码示例可参考 `code/` 文件夹。
5. 运行 `clean.bat` ，可以清理冗余的文件。

## 绘图方式参考

论文中的图像可以按用途分为三类：流程结构图、机理示意图和数据结果图。不同类型建议使用不同工具绘制。

- **DrawIO**：适合绘制整体技术路线图、问题求解流程图、数据处理流程图、模型结构图、指标体系图、决策树、评价体系框架图等非数据型图示。
- **TikZ**：适合绘制物理图、几何示意图、受力分析图、运动轨迹图、变量关系图、约束区域图、带公式标注的模型机理图。
- **Python/MATLAB**：适合绘制所有数据型图表，例如趋势、分布、误差、对比、相关性、灵敏度、网络和优化结果等。

数据图可以根据题型选择：

- **数据探索类**：折线图、散点图、柱状图、直方图、核密度图、分组箱线图、小提琴图、缺失值热力图、相关性热力图。
- **预测与拟合类**：真实值-预测值对比图、残差分布图、误差箱线图、误差热力图、多模型指标对比图、置信区间图。
- **评价与排序类**：雷达图、评分排名图、指标权重图、堆叠柱状图、聚类热力图、TOPSIS/熵权法结果对比图。
- **优化与灵敏度类**：算法收敛曲线、目标函数变化图、Pareto 前沿图、参数灵敏度曲线、资源分配图、方案对比图。
- **网络与流向类**：网络拓扑图、节点重要性图、OD 热力图、路径流量图、Sankey 流向图。
- **解释性分析类**：特征重要性图、SHAP 汇总图、SHAP 依赖图、贡献度分解图、局部解释图。

建议数据图优先使用 `matplotlib`、`seaborn`、`plotly`、`networkx` 等工具生成，并保存为 `pdf` 或 `png` 后插入论文。图像应包含清晰的标题、坐标轴标签、单位、图例和必要注释。

## DrawIO 图示绘制与命令行使用

本模板中的非数据型图示优先使用 DrawIO 绘制，例如整体技术路线图、子问题求解流程图、数据处理流程图、模型结构图、指标体系图、决策树等。折线图、柱状图、散点图、热力图等数据图不要用 DrawIO，应由 Python 或 MATLAB 代码生成。

### 命令行导出

本机可用 DrawIO CLI 一般为 `/opt/homebrew/bin/drawio`。为了兼容不同环境，推荐先自动探测命令：

```bash
DRAWIO_BIN="$(command -v drawio 2>/dev/null || command -v draw.io 2>/dev/null || command -v draw.io.exe 2>/dev/null || true)"
```

单张图导出：

```bash
"$DRAWIO_BIN" --export --format pdf --crop --output texfile/figures/fig_roadmap.pdf texfile/figures/fig_roadmap.drawio
```

批量导出 `texfile/figures/` 下所有 `.drawio`：

```bash
DRAWIO_BIN="$(command -v drawio 2>/dev/null || command -v draw.io 2>/dev/null || command -v draw.io.exe 2>/dev/null || true)"
if [ -z "$DRAWIO_BIN" ]; then
  echo "DrawIO command not found"
  exit 1
fi

for drawio_file in texfile/figures/*.drawio; do
  [ -e "$drawio_file" ] || continue
  pdf_file="${drawio_file%.drawio}.pdf"
  "$DRAWIO_BIN" --export --format pdf --crop --output "$pdf_file" "$drawio_file"
done
```

`--crop` 必须保留，用于裁剪 PDF 白边。导出完成后检查 PDF 是否非空：

```bash
ls -lh texfile/figures/*.pdf
```

### LaTeX 嵌入方式

在对应章节中使用 `figure` 环境引用导出的 PDF：

```latex
\begin{figure}[htbp]
	\centering
	\includegraphics[width=0.92\textwidth]{texfile/figures/fig_roadmap.pdf}
	\caption{整体技术路线图}
	\label{fig:overall-technical-route}
\end{figure}
```


### 绘图质量要求

- 节点文字保持简短，必要时使用两行，不在图中堆长句。
- 同类节点样式统一，箭头方向清晰，避免交叉和穿过核心节点。
- 配色使用低饱和度色彩，不使用过度阴影、渐变和装饰元素。
- DrawIO XML 中避免使用 `shadow=1`，命令行导出时容易出现节点渲染异常。
- 所有节点建议使用 `html=1`，换行使用 `&lt;br&gt;`。
- 特殊字符需要做 XML 转义：`<`、`>`、`&`、`"` 分别写成 `&lt;`、`&gt;`、`&amp;`、`&quot;`。

## TikZ 图示使用场景

物理图像、几何示意图、受力分析图、带公式变量标注的模型结构图，优先使用 TikZ 绘制。TikZ 适合需要精确坐标、角度、长度、方向箭头、约束区域、轨迹曲线和数学符号标注的图。

推荐分工：

- **DrawIO**：整体技术路线图、子问题流程图、数据处理流程图、指标体系图、决策树、概念框架图。
- **TikZ**：物理/几何示意图、受力分析图、运动轨迹图、算法流程图（含公式）、变量关系图、约束区域示意图。
- **Python/MATLAB**：折线图、柱状图、散点图、热力图、箱线图、误差曲线、灵敏度分析曲线等数据型图表。

基本原则：流程和架构用 DrawIO，物理和几何关系用 TikZ，实验结果和数据分布用代码绘图。

## 依赖宏包

模板已集成常用宏包：ctex、amsmath、amssymb、geometry、natbib、listings、graphicx、hyperref、booktabs、longtable、rotating、enumitem、caption、fancyhdr、titlesec 等。
