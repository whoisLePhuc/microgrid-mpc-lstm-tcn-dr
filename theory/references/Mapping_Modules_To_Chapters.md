# MAPPING: Module Files → Các Chương Tiểu Luận

**Mục đích:** Xác định chính xác nội dung từ 5 module files và design document sẽ được đưa vào chương nào.

---

## Tổng quan mapping

```
Module 1 (Nguồn)      → Chương 2 §2.1 + Chương 3 §3.2
Module 2 (LSTM-TCN)   → Chương 2 §2.3 + Chương 4 §4.1
Module 3 (MPC)        → Chương 2 §2.2 + Chương 3 §3.3 + Chương 4 §4.2
Module 4 (DR)         → Chương 2 §2.4 + Chương 3 §3.4 + Chương 4 §4.3
Module 5 (PMS)        → Chương 3 §3.1 + Chương 4 §4.4
Design Doc            → Chương 1 (gap/research questions) + Chương 3 §3.1 + Chương 5
Review Report         → Kiểm tra chéo, không đưa vào báo cáo
```

---

## CHƯƠNG 1: GIỚI THIỆU TỔNG QUAN

**Trạng thái:** Cần viết mới từ design document + tham khảo abstracts từ các bài báo gốc.

| Section | Nguồn | Ghi chú |
|---------|-------|---------|
| **1.1 Đặt vấn đề** | Design Doc §1.1, §1.2 | Viết lại từ overview system architecture + motivation |
| **1.2 Mục tiêu nghiên cứu** | Design Doc §1.0 (mục tiêu ở đầu file) | 3 mục tiêu chính |
| **1.3 Đối tượng và phạm vi** | Design Doc §1.3 (bảng kế thừa) | PV 20kW, Wind 10kW, Battery 50kWh, grid-connected |
| **1.4 Phương pháp nghiên cứu** | Design Doc §1.2 (luồng dữ liệu) | MPC + LSTM-TCN + DR, mô phỏng MATLAB/Simulink |
| **1.5 Research Gap** | Design Doc §1.3 (bảng so sánh với 2 papers) | Gap: không có paper nào kết hợp MPC+LSTM+DR cho PV-Wind-Battery grid-connected |
| **1.6 Cấu trúc báo cáo** | — | Viết mới, mô tả ngắn 6 chương |

**Nội dung chính cho 1.5 Research Gap (bảng so sánh):**

| Tiêu chí | Panda (Bài 1) | Limouni (Bài 2) | Đề tài |
|----------|:------------:|:--------------:|:------:|
| PV | ✅ | ✅ | ✅ |
| Wind | ❌ | ❌ | **✅** |
| MPC | ❌ (PSO) | ✅ | **✅** |
| LSTM-TCN | ❌ | ✅ | **✅** |
| DR (TOU + Peak/Valley) | ✅ | ❌ | **✅** |
| Grid-connected | ✅ | ❌ (standalone) | **✅** |

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

**Dung lượng dự kiến:** 15-20 trang
**Nguyên tắc:** Chỉ lấy phần **lý thuyết**, không lấy phần thông số đề tài hay algorithm.

### 2.1 Hệ thống PV–Wind–Battery Microgrid

| Subsection | Nguồn trong Module | Nội dung lấy |
|------------|-------------------|--------------|
| **2.1.1 Mô hình PV** | Module1 §1.1, §1.2, §1.3 | Lý thuyết PV (single-diode model, De Soto), **bỏ** bảng thông số ASW-250P (để dành cho Chương 3) |
| **2.1.2 Mô hình Wind Turbine** | Module1 §2.1, §2.2, §2.3, §2.4 | Lý thuyết: Betz limit, IEC 4-region power curve, wind shear power law. **Bỏ** bảng thông số (để Chương 3) |
| **2.1.3 Mô hình Battery** | Module1 §3.1, §3.2 | Coulomb counting, constraints (SOC, power). **Bỏ** thông số (để Chương 3) |
| **2.1.4 Cân bằng công suất** | Module1 §4.1 | Power balance equation, grid constraints |

### 2.2 Model Predictive Control (MPC)

| Subsection | Nguồn trong Module | Nội dung lấy |
|------------|-------------------|--------------|
| **2.2.1 Nguyên lý MPC** | Module3 §1, §2 | Định nghĩa, receding horizon, sơ đồ |
| **2.2.2 State-space model** | Module3 §3, §4, §5 | Boost converter model, Forward Euler, dạng tổng quát x(k+1)=Ax+Bu. **Bỏ** ma trận chi tiết (để Chương 3) |
| **2.2.3 Cost function và constraints** | Module3 §6, §7 | Dạng tổng quát, QP formulation, constraints categories. **Chỉ lấy lý thuyết, bỏ thông số** |
| **2.2.4 OSQP Solver** | Module3 §10 | Tổng quan solver, warm start |

### 2.3 LSTM-TCN Forecasting

| Subsection | Nguồn trong Module | Nội dung lấy |
|------------|-------------------|--------------|
| **2.3.1 LSTM cho chuỗi thời gian** | Module2 §2 | Cấu trúc LSTM cell, gates (forget, input, output) |
| **2.3.2 TCN residual blocks** | Module2 §3 | Causal conv, dilated conv, receptive field tính toán, residual block |
| **2.3.3 Kiến trúc lai LSTM-TCN** | Module2 §4 | Sequential LSTM→TCN, so sánh với parallel variant. **Bỏ** thông số neurons (để Chương 4) |

### 2.4 Demand Response trong năng lượng tái tạo

| Subsection | Nguồn trong Module | Nội dung lấy |
|------------|-------------------|--------------|
| **2.4.1 Price-based DR** | Module4 §1, §2, §3 | TOU, RTP, CPP, price elasticity, PEM. **Bỏ** bảng PEM số (để Chương 3) |
| **2.4.2 Incentive-based DR** | Module4 §1, §4 | Peak Clipping, Valley Filling, direct load control |
| **2.4.3 Mô hình hóa DR trong bài toán tối ưu** | Module4 §5 | Dạng tổng quát objective function có DR term. **Bỏ** thông số (để Chương 3) |

---

## CHƯƠNG 3: XÂY DỰNG MÔ HÌNH HỆ THỐNG

**Dung lượng dự kiến:** 12-15 trang
**Nguyên tắc:** Thông số cụ thể của đề tài, bảng số liệu, configuration.

### 3.1 Kiến trúc microgrid kết nối lưới

| Subsection | Nguồn | Nội dung |
|------------|-------|----------|
| **3.1.1 Sơ đồ tổng thể** | Module5 §1 + Design Doc §1.1 | Sơ đồ khối toàn hệ thống (PV-Wind-Battery-Grid-DR-MPC) |
| **3.1.2 PMS Super-modes** | Module5 §2 | EPM (Excess) vs DPM (Deficit), bảng điều kiện |

### 3.2 Mô hình hóa các thành phần

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **PV system** | Module1 §1.4 | **Bảng thông số ASW-250P**, số module, tổng công suất 20kWp |
| **Wind turbine** | Module1 §2.6 | **Bảng thông số**: Prated=10kW, Vcut-in=3, Vrated=12, Vcut-out=25, D=7m, Cp=0.45 |
| **Battery** | Module1 §3.4 | **Bảng thông số**: 50kWh, 120V, SoC 20-90%, η=0.95 |
| **Inverter & Grid** | Module1 §4.2, §4.3, §5 | Bảng tổng kết thông số |
| **Power balance** | Module1 §4.1 | Công thức P_PV+P_WT+P_bat+P_grid+P_DR = P_load |

### 3.3 Hàm mục tiêu và ràng buộc

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **Objective function** | Module3 §6.2 | **Công thức đầy đủ**: J = tracking terms + economic DR term |
| **State-space matrices** | Module3 §5.4 | Ma trận A (5×5), B (5×3), Bd (5×3) — chi tiết |
| **Constraints** | Module3 §7 | SOC, current, voltage, DR, power balance |
| **Weights table** | Module3 §6.4 | W_PV=10, W_bat=50, W_wind=10, W_DC=100, W_SOC=1 |

### 3.4 Tích hợp DR vào MPC

| Subsection | Nguồn | Nội dung |
|------------|-------|----------|
| **3.4.1 Mô hình TOU pricing** | Module4 §3.1 | Bảng giá 5 khung giờ + PEM matrix |
| **3.4.2 Threshold DR logic** | Module4 §4.2, §4.3 | Peak Clipping (α=0.15, threshold 80%), Valley Filling (β=0.10, threshold 30%) |
| **3.4.3 Sigmoid integration** | Module3 §4.4 (sigmoid) + Module4 §6.2 | Công thức sigmoid cho DR smooth transition |

---

## CHƯƠNG 4: THUẬT TOÁN ĐIỀU KHIỂN ĐỀ XUẤT

**Dung lượng dự kiến:** 15-18 trang
**Nguyên tắc:** Phần lõi của đề tài — pseudocode, flowcharts, architecture diagrams.

### 4.1 Thuật toán dự báo LSTM-TCN mở rộng

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **Kiến trúc mở rộng** | Module2 §4, §7 | Sequential LSTM(256→64) → TCN(3 blocks) → Dense(H×5) |
| **Input features** | Module2 §6.1 | GHI, Temp, **Wind Speed (mới)**, Load, **Price (mới)**, Time |
| **Output targets** | Module2 §6.2 | PV, Wind, Temp, Load, Price (5 targets cho MPC horizon) |
| **Sliding window** | Module2 §5 | Look-back=12 steps, horizon=1-4 steps |
| **Training algorithm** | Module2 §10 | Pseudocode: data prep → training loop → inference |
| **Hyperparameters** | Module2 §8 | Bảng hyperparameter tổng hợp |

### 4.2 Vòng lặp điều khiển MPC

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **MPC Algorithm** | Module3 §12.1 | Pseudocode chi tiết (đo → forecast → PMS → DR → sigmoid → LTV → QP → OSQP → apply) |
| **Lưu đồ MPC** | Module3 §12.2 | Flowchart |
| **Thông số MPC** | Module3 §11 | Inner loop (Ts=4μs, Np=2) + Outer loop (Ts=1h, Np=24) |
| **Sigmoid integration** | Module3 §4.4 | Công thức sigmoid cho từng nguồn |
| **OSQP solver** | Module3 §10 | Kiến trúc thực thi 2-core, warm start |

### 4.3 Lập lịch DR động

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **DR Logic Algorithm** | Module4 §6.1 | Pseudocode: 2-layer (price-based → threshold-based) |
| **DR Flowchart** | Module4 §6.3 | Sơ đồ DR decision |
| **Sigmoid cho DR** | Module4 §6.2 | Công thức sigmoid cho DR transition |
| **DR constraints** | Module4 §5.2 | Ràng buộc P_DR, ramp rate |

### 4.4 Lưu đồ thuật toán tổng thể

| Mục | Nguồn | Nội dung |
|-----|-------|----------|
| **Sequence diagram** | Module5 §10 | Sequence: LSTM→MPC→PMS→DR→Converters |
| **State machine** | Module5 §4 | PMS 6-mode state machine diagram |
| **Reference currents** | Module3 §9.1 | Bảng I_ref theo từng PMS mode |
| **Seamless transition** | Module5 §7 | Sigmoid smoothing, hysteresis |

---

## CHƯƠNG 5: MÔ PHỎNG VÀ KẾT QUẢ

**Trạng thái:** Cần viết sau khi chạy mô phỏng.
**Nguồn tham khảo:** Design Doc §7, §8 + Module Design.

| Section | Hướng dẫn nội dung |
|---------|-------------------|
| **5.1 Tham số hệ thống** | Lấy bảng tổng kết từ Module1 §5 + Module3 §11. Bảng thông số mô phỏng (MATLAB/Simulink) |
| **5.2 Các kịch bản** | 4-5 kịch bản: S1 baseline, S2 MPC only, S3 MPC+TOU, S4 MPC+Full DR. Thiết kế từ Design Doc §8.1 |
| **5.3 Kết quả** | VRI, cost saving, renewable utilization, settling time — vẽ biểu đồ so sánh giữa các kịch bản |
| **5.4 So sánh** | Bảng so sánh với 2 papers gốc |
| **5.5 Phân tích độ nhạy** | Battery capacity (25-100kWh), DR ratio (5-20%), forecast error (±5-20%) |

**Các KPI cần tính (từ Design Doc §8.2):**

| KPI | Công thức |
|-----|-----------|
| VRI | $\|V_{DC,ref} - V_{DC}\| / V_{DC,ref} \times 100\%$ |
| Cost saving | $(Cost_{baseline} - Cost_{proposed}) / Cost_{baseline} \times 100\%$ |
| Renewable utilization | $E_{renewable,used} / E_{renewable,available} \times 100\%$ |
| Peak reduction | $(P_{peak,before} - P_{peak,after}) / P_{peak,before} \times 100\%$ |
| Settling time | $t_s$ (ms) |

---

## CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

**Trạng thái:** Cần viết sau khi có kết quả mô phỏng.

| Section | Hướng dẫn nội dung |
|---------|-------------------|
| **6.1 Kết luận** | Tổng hợp kết quả Chương 5, trả lời các mục tiêu ở Chương 1 |
| **6.2 Hạn chế** | Điểm yếu từ Module review (perfect forecast assumption, threshold DR tĩnh, chưa có battery degradation) |
| **6.3 Hướng phát triển** | Tham khảo từ Module1→Module5 future work: hardware-in-the-loop, multi-agent RL, AC microgrid, real-time pricing |

---

## Bảng tương quan Module → Chương (tóm tắt)

```
Module File           | Chương 2 | Chương 3 | Chương 4 | Ghi chú
──────────────────────|──────────|──────────|──────────|──────────────────────
Module1_Source        | §2.1     | §3.2     | —        | Theory (C2) + Parameters (C3)
Module2_LSTM_TCN      | §2.3     | —        | §4.1     | Theory (C2) + Algorithm (C4)
Module3_MPC           | §2.2     | §3.3     | §4.2     | Theory (C2) + Model (C3) + Algorithm (C4)
Module4_DR            | §2.4     | §3.4     | §4.3     | Theory (C2) + Model (C3) + Algorithm (C4)
Module5_PMS           | —        | §3.1     | §4.4     | Model (C3) + Algorithm (C4) + State machine
Design Doc            | —        | §3.1     | —        | Overview, architecture diagrams
Review Report         | —        | —        | —        | Chỉ để kiểm tra, KHÔNG đưa vào báo cáo
```

---

## Nguyên tắc phân chia nội dung

```
Cùng một module file nhưng cần tách:
├── Lý thuyết (C2)  ← khái niệm, công thức tổng quát, verified từ literature
├── Mô hình (C3)    ← thông số cụ thể, bảng số liệu, configuration của đề tài
└── Thuật toán (C4) ← pseudocode, flowchart, implementation details
```

**Ví dụ với Module 3 (MPC):**
- §2.2: Lý thuyết MPC tổng quát (receding horizon, dạng QP)
- §3.3: State-space matrix A/B/Bd cụ thể, weights, constraints số
- §4.2: Pseudocode vòng lặp điều khiển, flowchart, OSQP solver config
