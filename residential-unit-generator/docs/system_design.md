# AI + Grasshopper 户型生成器 MVP — Grasshopper/Python 代码结构草案

目标：建立一套可重复运行、可验证、可扩展的标准户型生成系统。  
适用范围：矩形公寓/住宅单元 MVP，后续可扩展到异形边界、优化算法、BIM 输出。

---

## 1. 总体架构

```text
输入层
  input_config.json
  boundary curve
  entrance point
  room program
        ↓
配置解析层
  config_loader
        ↓
空间生成层
  rectangle utilities
  BSP splitter
  room assignment
  wall builder
        ↓
规则校验层
  hard rules
  soft rules
  warnings
        ↓
评分层
  area score
  room quality score
  circulation score
  rule compliance score
        ↓
批量生成层
  parameter sampler
  solution batch runner
        ↓
输出层
  Rhino blocks
  layers
  text labels
  JSON result
  CSV summary
        ↓
AI / MCP 协作层
  prompt templates
  script review prompts
  regression test prompts
```

---

## 2. 推荐目录结构

```text
residential-unit-generator/
│
├── README.md
├── gh/
│   ├── Residential_Unit_Generator.gh
│   ├── Residential_Unit_Batch.gh
│   └── scripts/
│       ├── config_loader.py
│       ├── rectangle_utils.py
│       ├── bsp_splitter.py
│       ├── room_assigner.py
│       ├── wall_builder.py
│       ├── rule_checker.py
│       ├── scorer.py
│       ├── result_builder.py
│       ├── rhino_writer.py
│       └── batch_runner.py
│
├── configs/
│   ├── default_3br.json
│   ├── compact_2br.json
│   └── sample_boundary.json
│
├── results/
│   ├── unit_A001.json
│   ├── batch_summary.csv
│   └── batch_report.md
│
├── tests/
│   ├── test_bsp_splitter.py
│   ├── test_rule_checker.py
│   ├── test_scorer.py
│   └── sample_inputs/
│
├── prompts/
│   ├── generate_initial_rules.md
│   ├── fix_generation_bug.md
│   ├── improve_scorer.md
│   └── review_grasshopper_python.md
│
└── docs/
    ├── system_design.md
    ├── data_schema.md
    └── roadmap.md
```

---

## 3. 核心数据结构

### 3.1 输入配置 JSON

```json
{
  "project_name": "standard_apartment_mvp",
  "unit_type": "3BR",
  "boundary": {
    "x": 0,
    "y": 0,
    "width": 12.0,
    "depth": 8.0
  },
  "building": {
    "floor_height": 2.9,
    "wall_thickness": 0.2,
    "entrance": {
      "position": "long_edge",
      "offset": 1.2,
      "side": "bottom"
    }
  },
  "program": [
    { "name": "living_room", "target_area": 22.0, "required": true },
    { "name": "kitchen", "target_area": 7.0, "required": true },
    { "name": "bedroom_main", "target_area": 13.0, "required": true },
    { "name": "bedroom_2", "target_area": 10.0, "required": true },
    { "name": "bathroom_wet", "target_area": 5.0, "required": true },
    { "name": "bathroom_dry", "target_area": 4.0, "required": true },
    { "name": "storage", "target_area": 3.0, "required": false }
  ],
  "constraints": {
    "min_area": {
      "bedroom_main": 11.0,
      "bedroom_2": 9.0,
      "bathroom_wet": 4.0,
      "bathroom_dry": 3.5
    },
    "max_aspect_ratio": 3.2,
    "max_corridor_width": 1.6,
    "min_corridor_width": 1.0,
    "max_dead_end_corridor": 1.8
  }
}
```

### 3.2 单个户型结果 JSON

```json
{
  "unit_id": "A001",
  "seed": 1234,
  "status": "valid",
  "total_area": 91.8,
  "usable_area": 76.4,
  "corridor_area": 5.2,
  "rooms": [
    {
      "id": "R01",
      "name": "bedroom_main",
      "area": 13.2,
      "width": 3.1,
      "depth": 4.3,
      "aspect_ratio": 1.39,
      "center": [6.2, 4.1],
      "polygon": [[0, 0], [3.1, 0], [3.1, 4.3], [0, 4.3]]
    }
  ],
  "doors": [
    {
      "from": "entrance",
      "to": "bedroom_main",
      "point": [1.2, 1.0],
      "width": 0.9
    }
  ],
  "warnings": [
    "bedroom_2 width is slightly under preferred width"
  ],
  "score": 0.82
}
```

---

## 4. Grasshopper 组件结构

### GH 01 — Input Definition

输入：

- Boundary Rectangle / Curve
- Entrance Point
- Wall Thickness
- Config JSON Path
- Random Seed
- Batch Count
- Generate Button

输出：

- Parsed Config
- Status
- Validation Messages

---

### GH 02 — BSP Generator

输入：

- Boundary Rect
- Program Areas
- Split Bias
- Seed

输出：

- Rectangles
- Room Metadata
- BSP Tree

---

### GH 03 — Room Assignment

输入：

- Rectangles
- Room Program

输出：

- Assigned Rooms
- Unassigned Spaces
- Area Deviation

---

### GH 04 — Wall Builder

输入：

- Rooms
- Wall Thickness
- Entrance Position
- Door Rules

输出：

- Room Polylines
- Wall Curves
- Door Locations

---

### GH 05 — Rule Checker

输入：

- Rooms
- Doors
- Constraints

输出：

- Pass/Fail
- Warnings
- Hard Failures
- Rule Report

---

### GH 06 — Scorer

输入：

- Rooms
- Doors
- Constraints

输出：

- Total Score
- Area Score
- Room Quality Score
- Circulation Score
- Compliance Score

---

### GH 07 — Rhino Writer

输入：

- Room Polylines
- Room Names
- Areas
- Door Locations
- Output Mode

输出：

- Rhino Blocks
- Layers
- Text Labels
- JSON Result

---

## 5. Python 脚本拆分

### 5.1 config_loader.py

职责：

- 读取 JSON 配置
- 校验必填字段
- 把配置转成 Grasshopper/Python 可用对象
- 返回错误信息

建议函数：

```python
def load_config(json_text):
    pass

def validate_config(config):
    pass

def get_program(config):
    pass
```

---

### 5.2 rectangle_utils.py

职责：

- 矩形几何计算
- 面积
- 中心点
- 长宽比
- 矩形相邻判断
- 合并/裁剪基础工具

建议函数：

```python
class Rect:
    def __init__(self, x, y, w, h):
        pass

    @property
    def area(self):
        pass

    @property
    def center(self):
        pass

    @property
    def aspect_ratio(self):
        pass

def split_horizontal(rect, split_ratio):
    pass

def split_vertical(rect, split_ratio):
    pass

def is_adjacent(rect_a, rect_b, tolerance=0.01):
    pass
```

---

### 5.3 bsp_splitter.py

职责：

- 按目标面积生成 BSP 分割
- 递归切分边界
- 控制长宽比
- 记录 split history

建议函数：

```python
def generate_bsp(root_rect, target_areas, seed=0, depth_limit=8):
    pass

def choose_split_direction(rect, remaining_area, max_aspect_ratio):
    pass

def make_split(rect, target_ratio, direction):
    pass
```

---

### 5.4 room_assigner.py

职责：

- 将 BSP 区域分配给房间
- 根据面积误差排序
- 处理非必需房间
- 生成 room metadata

建议函数：

```python
def assign_rooms(rectangles, program, seed=0):
    pass

def match_room_area(rect, room_type, min_area):
    pass

def build_room_objects(rectangles, assignment):
    pass
```

---

### 5.5 wall_builder.py

职责：

- 从房间边界生成墙体曲线
- 识别公共边作为墙
- 插入门洞
- 设置入口
- 输出 room polylines

建议函数：

```python
def build_walls(rooms, wall_thickness, entrance, door_rules):
    pass

def find_shared_edges(room_a, room_b):
    pass

def create_doors(rooms, entrance):
    pass

def create_room_polylines(rooms):
    pass
```

---

### 5.6 rule_checker.py

职责：

- 检查硬规则
- 检查软规则
- 返回 warnings / hard failures
- 输出报告

建议规则：

```python
def check_min_area(rooms, constraints):
    pass

def check_aspect_ratio(rooms, constraints):
    pass

def check_bathroom_not_dead_end(rooms):
    pass

def check_kitchen_has_window(room, boundary):
    pass

def check_no_illegal_adjacency(rooms, adjacency_rules):
    pass
```

---

### 5.7 scorer.py

职责：

- 对单个方案评分
- 输出分项分数和总分

建议函数：

```python
def score_unit(unit_result):
    pass

def area_efficiency_score(unit_result):
    pass

def room_quality_score(rooms, constraints):
    pass

def circulation_score(doors, rooms):
    pass

def compliance_score(warnings, failures):
    pass
```

---

### 5.8 batch_runner.py

职责：

- 批量生成不同 seed
- 收集结果
- 过滤硬失败
- 按分数排序
- 输出 JSON/CSV

建议函数：

```python
def generate_batch(config, count, seed_start=0):
    pass

def filter_valid(results):
    pass

def rank_results(results):
    pass

def write_summary(results, csv_path):
    pass
```

---

### 5.9 rhino_writer.py

职责：

- 创建 Rhino layers
- 写入 blocks
- 添加文字标注
- 保存 JSON
- 控制对象属性

建议函数：

```python
def ensure_layers(layer_names):
    pass

def write_room_blocks(rooms):
    pass

def write_doors(doors):
    pass

def write_labels(rooms):
    pass

def write_result_json(unit_result, path):
    pass
```

---

## 6. 第一批硬规则

MVP 先只放这些硬规则：

1. 所有必需房间必须存在。
2. 卧室面积不得小于最小值。
3. 卫生间面积不得小于最小值。
4. 房间长宽比不得超过最大值。
5. 入口必须可达。
6. 每个房间必须可达。
7. 卫生间不得死户。
8. 厨房必须靠近外墙或预留采光面。
9. 墙体不得完全重合导致无效几何。
10. 总有效面积不得低于目标面积下限。

---

## 7. 第一批软评分

1. 房间面积接近目标面积。
2. 走廊面积尽可能小。
3. 房间形状方正。
4. 从入口到房间距离短。
5. 主卧靠近主入口或优先采光面。
6. 卫生间靠近湿区核心。
7. 厨房靠近入户。
8. 房间边界对齐良好。
9. 过道宽度稳定。
10. 整体布局视觉清晰。

---

## 8. MVP 开发顺序

### Step 1 — 纯 Python 原型

先不接 Rhino UI。

目标：

- 输入 JSON
- 输出 JSON
- 能在本地跑 100 个方案

验证：

```text
python generate_batch.py configs/default_3br.json 100 results/
```

---

### Step 2 — Grasshopper Python 封装

把 Python 原型拆成可调用函数。

目标：

- GH 接收输入
- Python 返回 rooms / doors / scores / warnings

---

### Step 3 — Rhino 输出

目标：

- 每个房间一个 block
- 分层管理
- 标注名称和面积
- 保存 JSON

---

### Step 4 — 批量结果管理

目标：

- 自动生成 `batch_summary.csv`
- Top 50 结果排序
- 失败原因统计

---

### Step 5 — AI 协作接口

目标：

- AI 可以修改规则
- AI 可以修 bug
- AI 可以解释脚本
- AI 可以根据失败案例补测试

---

## 9. 关键验收标准

第一版成功标准：

- [ ] 输入 JSON 能生成基本平面
- [ ] 至少生成 100 个候选方案
- [ ] 每个方案都有唯一 ID
- [ ] 每个房间有面积、名称、多边形数据
- [ ] 硬规则失败会明确报出来
- [ ] 评分能排序方案
- [ ] Rhino 输出有 blocks 和 layers
- [ ] 结果 JSON 可被后续系统读取
- [ ] 修改规则后不会彻底重写全部代码
- [ ] 有 README 说明怎么运行

---

## 10. 后续扩展方向

1. 异形边界支持
2. 竖向交通系统
3. 楼梯/电梯核心生成
4. 家具自动布置
5. 日照分析
6. 能耗分析
7. 造价估算
8. Revit / Speckle 输出
9. 规范审查
10. 客户配置器 Web UI
11. Notion / Airtable dashboard
12. 多目标优化
13. 户型知识库
